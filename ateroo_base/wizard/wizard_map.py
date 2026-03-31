import requests
from odoo import models, fields, api


class WizardMap(models.TransientModel):
    _name = 'wizard.map'
    _inherit = 'map.tracking.mixin'
    _description = 'wizard.map'

    address = fields.Char()
    departure_latitude = fields.Float()
    departure_longitude = fields.Float()
    destination_latitude = fields.Float()
    destination_longitude = fields.Float()
    pick_id = fields.Many2one('delivery.picking')

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


