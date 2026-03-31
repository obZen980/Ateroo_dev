from odoo import models, fields


class ResUsers(models.Model):
    _inherit = 'res.users'

    delivery_agency_ids = fields.Many2many(
        comodel_name = 'delivery.agency',
        relation='res_user_delivery_agency_rel',
        column1='user_id',
        column2='agency_id',
    )