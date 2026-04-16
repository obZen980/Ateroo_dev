from odoo import models, fields


class ResCity(models.Model):
    _name = 'res.city'
    _description = 'City'

    name = fields.Char('Name', required=True)

