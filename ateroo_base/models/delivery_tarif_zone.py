from odoo import models, fields


class DeliveryTarifZone(models.Model):
    _name = 'delivery.tarif.zone'

    name = fields.Char('Name')
    price = fields.Float('Price')
