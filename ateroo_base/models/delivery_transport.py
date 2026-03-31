from odoo import  models, fields


class DeliveryTransport(models.Model):
    _name = 'delivery.transport'
    _description = 'Delivery transport mode'

    name = fields.Char('Name')
    coef_price = fields.Float('Price Coef. ')