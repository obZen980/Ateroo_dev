import requests
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
    duration = fields.Float(compute='_compute_road_distance', string='Estimated duration', store=True)
    display_duration = fields.Char(compute='_compute_display_duration')
    distance = fields.Float(compute='_compute_road_distance', string='Distance (km)', store=True)

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

    import requests

    @api.depends(
        'departure_id',
        'destination_id',
        'package_id.street',
        'package_id.recipient_street',
        'departure_id.agency_longitude',
        'departure_id.agency_latitude',
        'destination_id.agency_longitude',
        'destination_id.agency_latitude',
    )
    def _compute_road_distance(self):
        for rec in self:
            departure_longitude = False
            departure_latitude = False
            destination_longitude = False
            destination_latitude = False
            url = "https://nominatim.openstreetmap.org/search"
            if rec.departure_id == self.env.ref('ateroo_data.customer_location'):
                params = {"q": rec.package_id.street, "format": "json", "limit": 1}
                headers = {"User-Agent": "odoo-map-widget"}
                response = requests.get(url, params=params, headers=headers)
                if str(response.status_code).startswith('2'):
                    result = response.json()
                    if len(result):
                        departure_latitude = result[0]['lat']
                        departure_longitude = result[0]['lon']
            else:
                departure_latitude = rec.departure_id.agency_latitude
                departure_longitude = rec.departure_id.agency_longitude
            if rec.destination_id == self.env.ref('ateroo_data.customer_destination'):
                params = {"q": rec.package_id.recipient_street, "format": "json", "limit": 1}
                headers = {"User-Agent": "odoo-map-widget"}
                response = requests.get(url, params=params, headers=headers)
                if str(response.status_code).startswith('2'):
                    result = response.json()
                    if len(result):
                        destination_latitude = result[0]['lat']
                        destination_longitude = result[0]['lon']
            else:
                destination_latitude = rec.destination_id.agency_latitude
                destination_longitude = rec.destination_id.agency_longitude

            if departure_longitude and departure_latitude and destination_latitude and destination_longitude:
                url2 = f"http://router.project-osrm.org/route/v1/driving/{departure_longitude},{departure_latitude};{destination_longitude},{destination_latitude}"
                params = {"overview": "false"}
                response = requests.get(url2, params=params)
                data = response.json()
                route = data["routes"][0]
                distance_meters = route["distance"]
                duration_seconds = route["duration"]
                rec.distance = distance_meters/1000
                rec.duration = duration_seconds
            else:
                rec.distance = 0
                rec.duration = 0
