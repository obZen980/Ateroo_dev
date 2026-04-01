import json
from odoo import models, fields, _, api


class DeliveryTour(models.Model):
    _name = 'delivery.tour'
    _description = 'Delivery Tour'

    name = fields.Char('Name', default=_('New'))
    type = fields.Selection([('retrieve', 'Retrieve'), ('internal', 'Internal'), ('delivery', 'Delivery')], string='Type', required=True)
    driver_id = fields.Many2one('hr.employee', string='Driver', required=True)
    start_date = fields.Datetime('Tour date')
    state = fields.Selection([('new', 'New'), ('in_progress', 'In progress'), ('done', 'Done')], string='State', compute='compute_state', store=True)
    package_ids = fields.Many2many(
        'delivery.package', 'deliveyr_tour_package_rel', 'tour_id', 'package_id',
        string='Packages',
    )
    package_domain = fields.Char(compute='_compute_package_domain')

    @api.depends('package_ids', 'package_ids.delivery_picking_ids.state', 'package_ids.internal_picking_ids.state')
    def compute_state(self):
        for rec in self:
            delivery_picking = rec.package_ids.mapped('delivery_picking_ids')
            internal_picking = rec.package_ids.mapped('internal_picking_ids')
            if rec.type in ('retrieve', 'delivery'):
                if all(pick.state == 'done' for pick in delivery_picking):
                    rec.state = 'done'
                elif all(pick.state == 'none' for pick in delivery_picking):
                    rec.state = 'new'
                else:
                    rec.state = 'in_progress'
            else:
                if all(pick.state == 'done' for pick in internal_picking):
                    rec.state = 'done'
                elif all(pick.state == 'none' for pick in internal_picking):
                    rec.state = 'new'
                else:
                    rec.state = 'in_progress'

    @api.depends('type')
    def _compute_package_domain(self):
        for rec in self:
            domain = []
            if rec.type == 'retrieve':
                domain = [('state', '=', 'draft'), ('to_retrieve', '=', True)]
            elif rec.type == 'internal':
                domain = [('state', 'in', ['in_sort'])]
            elif rec.type == 'delivery':
                domain = ['|', ('state', 'in', ['ready', 'planned', 'delivery_deposit']), '&', ('state', 'in', ['draft', 'reception']), ('inter_region_available', '=', False)]
            rec.package_domain = json.dumps(domain)

    def fetch_package_pickings(self, package_id, tour_type):
        result = []
        package = self.env['delivery.package'].browse(package_id)
        pickings = []
        if tour_type == 'retrieve':
            pickings = package.delivery_picking_ids.filtered(lambda p: p.destination_id == package.agency_id)
        if tour_type == 'internal':
            pickings = package.internal_picking_ids
        if tour_type == 'delivery':
            pickings = package.delivery_picking_ids.filtered(lambda p: p.destination_id in (package.dest_agency_id, self.env.ref('ateroo_data.customer_destination')))
        for pick in pickings:
            result.append({
                'id': pick.id,
                'customer_name': package.partner_id.name,
                'customer_phone': package.phone or '',
                'customer_email': package.email or '',
                'customer_city': package.city or '',
                'customer_street': package.street or '',
                'customer_street2': package.street2 or '',
                'customer_landmark': package.landmark or '',
                'departure': pick.departure_id and pick.departure_id.name or '',
                'recipient_name': package.recipient_name or '',
                'recipient_phone': package.recipient_phone or '',
                'recipient_email': package.recipient_email or '',
                'recipient_city': package.recipient_city or '',
                'recipient_street': package.recipient_street or '',
                'recipient_street2': package.recipient_street2 or '',
                'recipient_landmark': package.recipient_landmark or '',
                'destination': pick.destination_id and pick.destination_id.name or '',
                'display_sender_address': pick.departure_id == self.env.ref('ateroo_data.customer_location'),
                'display_recipient_address': pick.destination_id == self.env.ref('ateroo_data.customer_destination'),
                'display_state': dict(pick._fields['state'].selection).get(pick.state) or '',
                'state': pick.state or '',
                'start_date': pick.start_date or '',
                'end_date': pick.end_date or ''
            })
        return result

    @api.model_create_multi
    def create(self, vals):
        res = super().create(vals)
        for rec in res:
            if not rec.name:
                rec.set_sequence()
        return res

    def set_sequence(self):
        self.ensure_one()
        sequence_obj = self.env['ir.sequence']
        self.name = sequence_obj.next_by_code('sequence.delivery.tour')
        return True



