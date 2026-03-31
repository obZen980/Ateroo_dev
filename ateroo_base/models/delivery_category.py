from odoo import models, fields


class DeliveryCategory(models.Model):
    _name = 'delivery.category'

    name = fields.Char('Name')
    description = fields.Text('Description')
    weight_limit = fields.Float("Weight limit")
    coef_price = fields.Float("Price coef.")