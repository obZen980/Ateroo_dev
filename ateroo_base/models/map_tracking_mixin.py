from odoo import models, fields, api


class MapTrackingMixin(models.AbstractModel):
    _name = 'map.tracking.mixin'
    _description = 'Map tracking'

    map_longitude = fields.Float('Longitude', digits=(10, 7), default=47.519622)
    map_latitude = fields.Float('Latitude', digits=(10, 7), default=-18.904565)
    map = fields.Char(compute='_compute_map')

    @api.depends('map_longitude', 'map_latitude')
    def _compute_map(self):
        for rec in self:
            rec.map = '/'.join([str(rec.map_latitude), str(rec.map_longitude)])
