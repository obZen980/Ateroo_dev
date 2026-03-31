from odoo import http
from odoo.http import request
import requests
import logging

_logger = logging.getLogger(__name__)


class OSMController(http.Controller):

    @http.route('/osm/autocomplete', type='json', auth='user')
    def osm_autocomplete(self, query):
        url = "https://nominatim.openstreetmap.org/search"
        params = {
            "q": query,
            "format": "json",
            "limit": 5,
            "addressdetails": 1
        }

        headers = {
            "User-Agent": "Odoo-OSM-Autocomplete"
        }
        response = requests.get(url, params=params, headers=headers, timeout=5)
        if str(response.status_code).startswith('2'):
            return response.json()
        else:
            _logger.error('Error %s on OSM request' % (response.status_code,))
        return []

    @http.route('/osm/geocode', type='json', auth='user')
    def osm_geocode(self, address):
        url = "https://nominatim.openstreetmap.org/search"
        params = {
            "q": address,
            "format": "json",
            "limit": 1
        }
        headers = {
            "User-Agent": "odoo-map-widget"
        }
        response = requests.get(url, params=params, headers=headers)
        if str(response.status_code).startswith('2'):
            return response.json()
        return None
