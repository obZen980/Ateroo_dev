from odoo import models, fields, api


class DeliveryPicking(models.Model):
    _name = 'delivery.picking'
    _description = 'Delivery picking'

    sequence = fields.Integer('Sequence', default=0)
    type = fields.Selection([('delivery', 'Delivery'), ('internal', 'Internal operation')], string='Operation type')
    departure_id = fields.Many2one('delivery.agency', 'departure', required=True)
    destination_id = fields.Many2one('delivery.agency', 'Destination', required=True)
    package_id = fields.Many2one('delivery.package', 'Package')
    start_date = fields.Datetime('Start Date')
    end_date = fields.Datetime('End date')
    state = fields.Selection([('none', 'None'), ('in_progress', 'In progress'), ('done', 'Done')], string='State', default='none')
    duration = fields.Float(compute='_compute_duration', store=True)
    display_duration = fields.Char(compute='_compute_display_duration')
    internal_domain = fields.Char(compute='_compute_internal_domain')

    @api.depends('start_date', 'end_date')
    def _compute_duration(self):
        for rec in self:
            if rec.start_date and rec.end_date:
                rec.duration = (rec.end_date - rec.start_date).total_seconds()
            else:
                rec.duration = 0

    def _compute_display_duration(self):
        for rec in self:
            if rec.duration:
                hours = int(rec.duration / 3600)
                minutes = int((rec.duration % 3600) / 60)
                display_duration = 0
                if hours and minutes:
                    display_duration = f"{hours}h {minutes}m"
                elif hours and not minutes:
                    display_duration = f"{hours}h"
                elif minutes and not hours:
                    display_duration = f"{minutes}m"
                rec.display_duration = display_duration
            else:
                rec.display_duration = False

    def action_start(self):
        self.ensure_one()
        self.state = 'in_progress'
        self.start_date = fields.Datetime.now()
        return True

    def action_done(self):
        self.ensure_one()
        self.state = 'done'
        self.end_date = fields.Datetime.now()
        if self.destination_id == self.package_id.agency_id:
            self.package_id.action_confirm()
        elif self.destination_id == self.package_id.dest_agency_id:
            self.package_id.action_delivery_in_deposit()
        elif self.destination_id == self.env.ref('ateroo_data.customer_destination'):
            self.package_id.action_delivered()
        return True

    def _compute_internal_domain(self):
        for rec in self:
            if rec.package_id.agency_id:
                rec.internal_domain = [('id', 'child_of', rec.package_id.agency_id.id)]
            else:
                rec.internal_domain = []
