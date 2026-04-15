import requests
from odoo import models, fields, api


class WizardMap(models.TransientModel):
    _name = 'wizard.map'
    _inherit = 'map.tracking.mixin'
    _description = 'wizard.map'

    @api.model
    def _default_agency(self):
        if self.env.context.get('model', False) == 'delivery.agency' and self.env.context.get('record_id', False):
            return self.env['delivery.agency'].browse(self.env.context['record_id'])
        return False

    address = fields.Char()
    departure_latitude = fields.Float()
    departure_longitude = fields.Float()
    destination_latitude = fields.Float()
    destination_longitude = fields.Float()
    latitude = fields.Float()
    longitude = fields.Float()
    agency_id = fields.Many2one('delivery.agency', default=_default_agency)
    pick_id = fields.Many2one('delivery.picking')

    @api.onchange('agency_id')
    def onchange_agency_id(self):
        if self.agency_id:
            self.latitude = self.agency_id.agency_latitude
            self.longitude = self.agency_id.agency_longitude

    @api.onchange('pick_id')
    def onchange_pick(self):
        if self.pick_id.departure_id == self.env.ref('ateroo_data.customer_location'):
            url = "https://nominatim.openstreetmap.org/search"
            params = {"q": self.pick_id.package_id.street, "format": "json", "limit": 1}
            headers = {"User-Agent": "odoo-map-widget"}
            response = requests.get(url, params=params, headers=headers)
            if str(response.status_code).startswith('2'):
                result = response.json()
                self.departure_latitude = result[0]['lat']
                self.departure_longitude = result[0]['lon']
        else:
            self.departure_latitude = self.pick_id.departure_id.agency_latitude
            self.departure_longitude = self.pick_id.departure_id.agency_longitude
        if self.pick_id.destination_id == self.env.ref('ateroo_data.customer_destination'):
            url = "https://nominatim.openstreetmap.org/search"
            params = {"q": self.pick_id.package_id.recipient_street, "format": "json", "limit": 1}
            headers = {"User-Agent": "odoo-map-widget"}
            response = requests.get(url, params=params, headers=headers)
            if str(response.status_code).startswith('2'):
                result = response.json()
                self.destination_latitude = result[0]['lat']
                self.destination_longitude = result[0]['lon']
        else:
            self.destination_latitude = self.pick_id.destination_id.agency_latitude
            self.destination_longitude = self.pick_id.destination_id.agency_longitude

    def save(self):
        if self._context.get('model') and self._context.get('record_id') and self._context.get('long_field') and self._context.get('lat_field'):
            record = self.env[self._context.get('model')].browse(self._context['record_id'])
            record.write({
                self._context['long_field']: self.longitude,
                self._context['lat_field']: self.latitude
            })
        return {'type': 'ir.actions.client', 'tag': 'soft_reload'}
