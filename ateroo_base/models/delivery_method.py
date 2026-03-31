from odoo import models, fields


class DeliveryMethod(models.Model):
    _name = 'delivery.method'
    _description = 'Delivery method'

    name = fields.Char('Name', required=True)
    coef_price = fields.Float('Price Coef. ')
    inter_region_available = fields.Boolean('Inter region available?', default=True)
