from odoo import models, fields


class ResPartner(models.Model):
    _inherit = 'res.partner'

    ateroo_customer_type = fields.Selection([
        ('particular', 'Particular'),
        ('e_commerce', 'E-commerce'),
        ('company', 'Company')], string='Customer Type'
    )