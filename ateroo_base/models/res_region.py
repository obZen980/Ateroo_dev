from odoo import models, fields


class ResRegion(models.Model):
    _name = 'res.region'
    _description = 'Region'

    name = fields.Char('Name', required=True)