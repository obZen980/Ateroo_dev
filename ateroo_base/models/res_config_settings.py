from odoo import models, fields, api


class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    package_product_id = fields.Many2one(
        'product.template',
        string='Product package',
        config_parameter='ateroo_base.package.product',
        help='Used for invoicing delivery package'
    )
    secret_key = fields.Char(
        string='Secret key for barcode',
        config_parameter='ateroo_base.secret.key',
    )

    @api.model
    def get_values(self):
        res = super(ResConfigSettings, self).get_values()
        IrConfigParameter = self.env['ir.config_parameter'].sudo()
        product = IrConfigParameter.get_param('ateroo_base.package.product')
        secret_key = IrConfigParameter.get_param('ateroo_base.secret.key')
        if product:
            res.update({'package_product_id': int(product)})
        if secret_key:
            res.update({'secret_key': secret_key})
        return res

    def set_values(self):
        super().set_values()
        IrConfigParameter = self.env['ir.config_parameter'].sudo()
        IrConfigParameter.set_param("ateroo_base.package.product", self.package_product_id.id)
        IrConfigParameter.set_param("ateroo_base.secret.key", self.secret_key)
