from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError
from datetime import date, timedelta
from odoo.tools import float_round
from jose import jwt
import zlib
import re
import pytz

STATES = [
    ('draft', 'Draft'),
    ('reception', 'Reception'),
    ('in_sort', 'In sorting'),
    ('ready', 'Ready for delivery'),
    ('planned', 'Planned'),
    ('delivery_in_progress', 'Delivery in progress'),
    ('delivery_deposit', 'Delivered in deposit'),
    ('delivered', 'Delivered'),
]

PARTNER_ADDRESS_FIELDS_TO_SYNC = [
    'street',
    'street2',
    'phone',
    'email',
    'city',
    'landmark',
    'region_id'
]


class DeliveryPackage(models.Model):
    _name = 'delivery.package'
    _description = 'Delivery package'
    _inherit = ['image.mixin',  'mail.thread', 'mail.activity.mixin', 'map.tracking.mixin']
    _rec_name = 'name'
    _order = 'create_date desc'

    name = fields.Char('Description', required=True)
    delivery_method_id = fields.Many2one('delivery.method', 'Delivery method', tracking=True)
    to_retrieve = fields.Boolean('To retrieve', tracking=True)
    cash_on_delivery = fields.Boolean('Cash on delivery')
    sequence = fields.Char('Sequence', copy=False)
    network = fields.Selection([('intra_urban', 'Intra urban'), ('inter_region', 'Inter Region')], string='Network', default='intra_urban')
    inter_region_available = fields.Boolean(related='delivery_method_id.inter_region_available')

    agency_id = fields.Many2one('delivery.agency', 'Origin agency', domain=[('parent_id', '=', False)], tracking=True)
    deposit_id = fields.Many2one('delivery.agency', 'Deposit center', domain="[('id', 'child_of', agency_id)]")
    dest_agency_id = fields.Many2one('delivery.agency', 'Dest. agency', tracking=True)
    dest_deposit_id = fields.Many2one('delivery.agency', 'Dest. deposit center', domain="[('id', 'child_of', dest_agency_id)]")

    partner_id = fields.Many2one('res.partner', 'Customer', tracking=True)
    customer_type = fields.Selection([
        ('particular', 'Particular'),
        ('e_commerce', 'E-commerce'),
        ('company', 'Company')], related='partner_id.ateroo_customer_type')
    sender_name = fields.Char('Name', tracking=True)
    phone = fields.Char('Phone', tracking=True, compute='_compute_partner_address_values', inverse='_set_partner_address', readonly=False, store=True)
    email = fields.Char('Email', compute='_compute_partner_address_values', inverse='_set_partner_address', readonly=False, store=True)
    city = fields.Char('City', compute='_compute_partner_address_values', inverse='_set_partner_address', readonly=False, store=True)
    street = fields.Char('Street', compute='_compute_partner_address_values', inverse='_set_partner_address', readonly=False, store=True)
    street2 = fields.Char('Street2', compute='_compute_partner_address_values', inverse='_set_partner_address', readonly=False, store=True)
    landmark = fields.Char('Landmark', compute='_compute_partner_address_values', inverse='_set_partner_address', readonly=False, store=True)
    region_id = fields.Many2one('res.region', string='Region', compute='_compute_partner_address_values', inverse='_set_partner_address', readonly=False, store=True)
    sender_note = fields.Text('Note')
    recipient_partner_id = fields.Many2one('res.partner', 'Recipient', tracking=True)
    recipient_phone = fields.Char('Phone', tracking=True, compute='_compute_recipient_partner_address_values', inverse='_set_partner_recipient_address', readonly=False, store=True)
    recipient_email = fields.Char('Email', compute='_compute_recipient_partner_address_values', inverse='_set_partner_recipient_address',  readonly=False, store=True)
    recipient_city = fields.Char('City', compute='_compute_recipient_partner_address_values', inverse='_set_partner_recipient_address', readonly=False, store=True, tracking=True)
    recipient_street = fields.Char('Street', compute='_compute_recipient_partner_address_values',  inverse='_set_partner_recipient_address', readonly=False, store=True, tracking=True)
    recipient_street2 = fields.Char('Street2', compute='_compute_recipient_partner_address_values',  inverse='_set_partner_recipient_address', readonly=False, store=True)
    recipient_landmark = fields.Char('Landmark', compute='_compute_recipient_partner_address_values',  inverse='_set_partner_recipient_address', readonly=False, store=True)
    recipient_region_id = fields.Many2one('res.region', string='Region', compute='_compute_recipient_partner_address_values',  inverse='_set_partner_recipient_address', readonly=False, store=True)
    recipient_note = fields.Text('Note')

    state = fields.Selection(STATES, string='State', default='draft', tracking=True)
    category_id = fields.Many2one('delivery.category', 'Type', compute='_compute_category', store=True, readonly=False, tracking=True)
    date = fields.Datetime('Delivery date', tracking=True)
    date_planned = fields.Datetime('Delivery date planned', tracing=True)

    weight = fields.Float('Weight', tracking=True, required=True, default=0.5)
    height = fields.Float('Height', tracking=True)
    width = fields.Float('Width', tracking=True)
    length = fields.Float('Length', tracking=True)
    display_size = fields.Char('Size', compute='_compute_display_size')
    volume = fields.Float('Volume', compute='_compute_volume', store=True)
    volumetric_weight = fields.Float('Volumetric weight', compute='compute_volumetric_weight')

    package_price = fields.Float('Package price', default=0.0)
    include_package_price = fields.Boolean('Inclure le prix du colis')
    amount_total = fields.Float('Amount total', compute='_compute_amount_total', store=True)
    amount_distance = fields.Float('Amount per distance', compute='_compute_amount_per_distance', store=True, readonly=False)
    amount_region = fields.Float('Amount inter region', compute='_compute_amount_region', store=True, readonly=False)
    include_amount_distance = fields.Boolean('Include distance amount?')
    pricelist_id = fields.Many2one('product.pricelist', 'Pricelist', ondelelte='set null')
    product_tmpl_id = fields.Many2one('product.template', 'Product', ondelete='set null')

    currency_id = fields.Many2one('res.currency', compute='_compute_currency')

    image_2 = fields.Image("Image", max_width=1920, max_height=1920)
    image_3 = fields.Image("Image", max_width=1920, max_height=1920)
    image_4 = fields.Image("Image", max_width=1920, max_height=1920)
    image_selector = fields.Image("Image", max_width=1920, max_height=1920)

    barcode = fields.Char("Barcode data", copy=False)
    token = fields.Char("Token", copy=False)

    invoice_ids = fields.Many2many('account.move', 'package_id', 'move_id', string='Invoices')
    invoice_count = fields.Integer('Invoice count', compute='_compute_invoice_count')

    current_location_id = fields.Many2one('delivery.agency', compute='_compute_current_location', tracking=True, string='Current location', store=True)
    delivery_picking_ids = fields.One2many('delivery.picking', 'package_id', ondelete='cascade', string='Routes', domain=[('type', '=', 'delivery')])
    internal_picking_ids = fields.One2many('delivery.picking', 'package_id', ondelete='cascade', string='Internal operations', domain=[('type', '=', 'internal')])

    @api.model_create_multi
    def create(self, vals):
        res = super().create(vals)
        for rec in res:
            if not rec.sequence:
                rec.set_sequence()
            if not res.token:
                rec.set_token()
            if not res.barcode and res.sequence:
                rec.set_barcode()
        return res

    @api.depends('width', 'length', 'height')
    def _compute_volume(self):
        for rec in self:
            rec.volume = rec.width * rec.height * rec.length

    @api.depends('state', 'delivery_picking_ids.state', 'internal_picking_ids.state')
    def _compute_current_location(self):
        for rec in self:
            location = self.env.ref('ateroo_data.customer_location', raise_if_not_found=False)
            if rec.state == 'reception' and rec.agency_id:
                location = rec.agency_id
            elif rec.state in ['in_sort', 'ready', 'planned', 'delivery_in_progress']:
                location = rec.agency_id
                internal_pickings = rec.internal_picking_ids\
                    .filtered(lambda pick: pick.state == 'done')\
                    .sorted(key=lambda pick: (pick.sequence, pick.create_date))
                if internal_pickings:
                    location = internal_pickings[-1].destination_id
            elif rec.state == 'delivery_deposit':
                location = rec.dest_agency_id
            elif rec.state in ['delivered', 'paid', 'pending_payment']:
                location = self.env.ref('ateroo_data.customer_destination', raise_if_not_found=False)
            rec.current_location_id = location and location.id or False

    @api.depends('weight')
    def _compute_category(self):
        categories = self.env['delivery.category'].search([('weight_limit', '!=', False)], order='weight_limit asc')
        for rec in self:
            if all(rec.weight > categ.weight_limit for categ in categories):
                palette = self.env.ref('ateroo_data.delivery_category_palette', raise_if_not_found=False)
                rec.category_id = palette.id if palette else False
            for categ in categories:
                if rec.weight <= categ.weight_limit:
                    rec.category_id = categ.id
                    break

    @api.depends('partner_id')
    def _compute_partner_address_values(self):
        for rec in self:
            rec.update(rec._prepare_address_values_from_partner(rec.partner_id, 'sender'))

    def _set_partner_address(self):
        for rec in self:
            for f in PARTNER_ADDRESS_FIELDS_TO_SYNC:
                if not rec.partner_id[f] and rec[f]:
                    rec.partner_id[f] = rec[f]

    @api.depends('recipient_partner_id')
    def _compute_recipient_partner_address_values(self):
        for rec in self:
            rec.update(rec._prepare_address_values_from_partner(rec.recipient_partner_id, 'recipient'))

    def _set_partner_recipient_address(self):
        for rec in self:
            for f in PARTNER_ADDRESS_FIELDS_TO_SYNC:
                if not rec.partner_id[f] and rec['recipient_'+f]:
                    rec.recipient_partner_id['recipient_' + f] = rec[f]

    @api.depends('width', 'height', 'length')
    def _compute_display_size(self):
        for rec in self:
            length = str(rec.length) + ' cm'
            width = str(rec.width) + ' cm'
            height = str(rec.height) + ' cm'
            rec.display_size = f"{length} x {width} x {height}"

    @api.depends('pricelist_id')
    def _compute_currency(self):
        for rec in self:
            if rec.pricelist_id:
                rec.currency_id = rec.pricelist_id.currency_id.id
            else:
                rec.currency_id = self.env.company.currency_id.id

    def compute_volumetric_weight(self):
        for rec in self:
            weight_volume = rec.volume / 5000
            rec.volumetric_weight = rec.weight if rec.weight >= weight_volume else weight_volume

    @api.depends('amount_distance', 'amount_region', 'package_price', 'include_package_price', 'include_amount_distance')
    def _compute_amount_total(self):
        for rec in self:
            amount_total = 0
            if rec.include_amount_distance:
                amount_total += rec.amount_distance
            if rec.include_package_price:
                amount_total += rec.package_price
            if rec.amount_region:
                amount_total += rec.amount_region
            rec.amount_total = amount_total

    @api.depends('delivery_picking_ids.distance')
    def _compute_amount_per_distance(self):
        pricelist = self.env['ir.config_parameter'].get_param('ateroo_base.pricelist.distance')
        pricelist = pricelist and self.env['product.pricelist'].browse(int(pricelist)) or False
        product_distance = self.env.ref('ateroo_data.product_distance', raise_if_not_found=False)
        for rec in self:
            if rec.delivery_picking_ids and pricelist and product_distance:
                delivery_pickings = rec.delivery_picking_ids.filtered(lambda pick: pick.departure_id != rec.agency_id and pick.destination_id != rec.dest_agency_id)
                distance = sum(delivery_pickings.mapped('distance'))
                price_unit = pricelist._get_product_price(product_distance, distance, product_distance.uom_id)
                rec.amount_distance = float_round(price_unit * distance, precision_digits=0)
            else:
                rec.amount_distance = 0

    @api.depends('weight', 'volume', 'package_price', 'pricelist_id', 'agency_id', 'dest_agency_id', 'network')
    def _compute_amount_region(self):
        for rec in self:
            delivery_price = 0
            if rec.network != 'inter_region':
                rec.amount_region = 0
                continue
            if rec.product_tmpl_id:
                quantity = rec.volumetric_weight
                price_unit = rec.pricelist_id._get_product_price(rec.product_tmpl_id.product_variant_id, quantity, rec.product_tmpl_id.uom_id)
                delivery_price = float_round(price_unit * quantity, precision_digits=0)
            rec.amount_region = delivery_price

    def _compute_invoice_count(self):
        for rec in self:
            rec.invoice_count = len(rec.invoice_ids)

    @api.constrains('weight')
    def _check_weight_valid(self):
        for rec in self:
            if not rec.weight or rec.weight <= 0:
                raise UserError(_('Weight should be above 0.'))

    def _prepare_address_values_from_partner(self, partner, partner_type='sender'):
        if partner_type == 'sender':
            if any(partner[f] for f in PARTNER_ADDRESS_FIELDS_TO_SYNC):
                values = {f: partner[f] for f in PARTNER_ADDRESS_FIELDS_TO_SYNC}
            else:
                values = {f: self[f] for f in PARTNER_ADDRESS_FIELDS_TO_SYNC}
            return values
        elif partner_type == 'recipient':
            if any(partner[f] for f in PARTNER_ADDRESS_FIELDS_TO_SYNC):
                values = {'recipient_' + f: partner[f] for f in PARTNER_ADDRESS_FIELDS_TO_SYNC}
            else:
                values = {'recipient_' + f: self['recipient_' + f] for f in PARTNER_ADDRESS_FIELDS_TO_SYNC}
            return values

    def set_sequence(self):
        self.ensure_one()
        sequence_obj = self.env['ir.sequence']
        self.sequence = sequence_obj.next_by_code('sequence.delivery.package')
        return True

    def create_token(self, data: dict, secret_key: str):
        to_encode = data.copy()
        algorithm = 'HS256'
        encoded_jwt = jwt.encode(to_encode, secret_key, algorithm=algorithm)
        return encoded_jwt

    def set_token(self):
        secret_key = self.env['ir.config_parameter'].sudo().get_param('ateroo_base.secret.key')
        secret_key = secret_key or 'ATEROO'
        token = self.create_token(
            data={"sub": '%s' % (self.sequence,)}, secret_key=secret_key
        )
        self.token = token
        return True

    def set_barcode(self):
        for rec in self:
            if rec.sequence:
                sequence = re.findall(r'\d+', rec.sequence)[0]
                crc = zlib.crc32(sequence.encode('utf-8'))
                base = str(abs(crc))[:12].zfill(12)
                checksum = self._ean13_checksum(base)
                rec.barcode = base + checksum
            else:
                rec.barcode = False

    def _ean13_checksum(self, code12):
        digits = [int(d) for d in code12]
        total = sum(digits[::2]) + sum(digits[1::2]) * 3
        return str((10 - total % 10) % 10)

    def action_print(self):
        self.ensure_one()
        xml_id = 'ateroo_base.report_delivery_package_label'
        if not xml_id:
            raise UserError(_('Unable to find report template for %s format', self.print_format))
        report_action = self.env.ref(xml_id).report_action(None, data=False,  config=False)
        report_action.update({'close_on_report_download': True})
        return report_action

    def _prepare_route_vals(self, departure, destination):
        return {
            'type': 'delivery',
            'departure_id': departure.id,
            'destination_id': destination.id
        }

    def action_generate_routes(self):
        self.ensure_one()
        routes = []
        if self.to_retrieve:
            routes.append(self.env.ref('ateroo_data.customer_location'))
        routes.append(self.agency_id)
        routes.append(self.dest_agency_id)
        # if self.recipient_street:
        routes.append(self.env.ref('ateroo_data.customer_destination'))
        routes = list(filter(lambda l: l, routes))
        routes = list(zip(routes, routes[1:]))
        result = list(map(lambda item: (0, 0, self._prepare_route_vals(item[0], item[1])), routes))
        self.delivery_picking_ids = result
        return True

    def action_confirm(self):
        for rec in self:
            rec.state = 'reception'
        return True

    @api.model
    def calculate_date_category(self, datetime):
        """
        Assigns given datetime to one of the following categories:
        - "before"
        - "yesterday"
        - "today"
        - "day_1" (tomorrow)
        - "day_2" (the day after tomorrow)
        - "after"

        The categories are based on current user's timezone (e.g. "today" will last
        between 00:00 and 23:59 local time). The datetime itself is assumed to be
        in UTC. If the datetime is falsy, this function returns "".
        """
        start_today = fields.Datetime.context_timestamp(self.env.user, fields.Datetime.now()).replace(hour=0, minute=0, second=0, microsecond=0)

        start_yesterday = start_today + timedelta(days=-1)
        start_day_1 = start_today + timedelta(days=1)
        start_day_2 = start_today + timedelta(days=2)
        start_day_3 = start_today + timedelta(days=3)

        date_category = ""

        if datetime:
            datetime = datetime.astimezone(pytz.UTC)
            if datetime < start_yesterday:
                date_category = "before"
            elif datetime >= start_yesterday and datetime < start_today:
                date_category = "yesterday"
            elif datetime >= start_today and datetime < start_day_1:
                date_category = "today"
            elif datetime >= start_day_1 and datetime < start_day_2:
                date_category = "day_1"
            elif datetime >= start_day_2 and datetime < start_day_3:
                date_category = "day_2"
            else:
                date_category = "after"

        return date_category

    @api.onchange('agency_id', 'dest_agency_id', 'product_tmpl_id')
    def onchange_agency(self):
        if self.agency_id and self.dest_agency_id and self.product_tmpl_id:
            pricelist = self.env['product.pricelist'].search([
                ('orig_zone_id', '=', self.agency_id.zone_id.id),
                ('dest_zone_id', '=', self.dest_agency_id.zone_id.id)
            ])
            pricelist = pricelist.filtered(lambda p: self.product_tmpl_id in p.item_ids.mapped('product_tmpl_id'))
            if pricelist:
                self.pricelist_id = pricelist
        else:
            self.pricelist_id = False

    def _prepare_invoice_vals(self):
        return {
            'partner_id': self.partner_id.id,
            'delivery_date': self.date,
            'currency_id': self.currency_id.id,
            'move_type': 'out_invoice',
        }

    def _prepare_invoice_line_vals(self):
        quantity = self.volumetric_weight
        package_product = self.env['ir.config_parameter'].sudo().get_param('ateroo_base.package.product')
        package_product = package_product and self.env['product.product'].browse(int(package_product)) or False
        product_distance = self.env.ref('ateroo_data.product_distance', raise_if_not_found=False)
        product_distance = product_distance and self.env['product.product'].browse(int(product_distance)) or False
        price = self.pricelist_id._get_product_price(self.product_tmpl_id.product_variant_id, quantity, self.product_tmpl_id.uom_id)
        vals = list()
        vals.append((0, 0, {
            'product_id': self.product_tmpl_id.product_variant_id.id,
            'quantity': quantity,
            'product_uom_id': self.product_tmpl_id.uom_id.id,
            'price_unit': price,
        }))
        if self.package_price and self.include_package_price and package_product:
            vals.append((0, 0, {
                'product_id': package_product.id,
                'name': self.name,
                'quantity': 1,
                'product_uom_id': package_product.uom_id.id,
                'price_unit': self.package_price
            }))
        if self.amount_distance and self.include_amount_distance and product_distance:
            vals.append((0, 0, {
                'product_id': product_distance.id,
                'name': self.name,
                'quantity': 1,
                'product_uom_id': product_distance.uom_id.id,
                'price_unit': self.amount_distance
            }))
        return vals

    def action_in_sort(self):
        self.state = 'in_sort'
        return True

    def action_create_invoice(self):
        if not self.partner_id:
            raise ValidationError(_('Partner is required to create invoice.'))
        if not self.product_tmpl_id:
            raise ValidationError(_('Product is required to create invoice.'))
        line_vals = self._prepare_invoice_line_vals()
        vals = self._prepare_invoice_vals()
        vals.update({'invoice_line_ids': line_vals})
        invoice = self.env['account.move'].create(vals)
        self.invoice_ids = [(4, invoice.id)]
        return {
                'name': _('Invoice'),
                'view_mode': 'form',
                'res_model': 'account.move',
                'res_id': invoice.id,
                'type': 'ir.actions.act_window',
                'target': 'current',
        }

    def action_view_invoice(self):
        return {
            'name': _('Invoices'),
            'view_mode': 'list,form',
            'res_model': 'account.move',
            'domain': [('id', 'in', self.invoice_ids.ids)],
            'type': 'ir.actions.act_window',
            'target': 'current',
        }

    def action_ready(self):
        self.state = 'ready'
        return True

    def action_planned(self):
        self.state ='planned'
        return True

    def action_delivery_in_progress(self):
        self.state = 'delivery_in_progress'
        return True

    def action_delivery_in_deposit(self):
        self.state = 'delivery_deposit'
        return True

    def action_delivered(self):
        self.state = 'delivered'
        return True

    def action_returned(self):
        self.state = 'returned'
        return True

    @api.onchange('delivery_method_id')
    def onchange_delivery_method(self):
        if not self.inter_region_available:
            self.dest_agency_id = False
            self.agency_id = False
            self.network = 'intra_urban'
            self.to_retrieve = True

    @api.onchange('network')
    def onchange_network(self):
        self.dest_agency_id = False