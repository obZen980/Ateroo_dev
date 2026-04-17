from odoo import models, fields, api


class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    package_product_id = fields.Many2one(
        'product.template',
        string='Product package',
        config_parameter='ateroo_base.package.product',
        help='Used for invoicing delivery package'
    )
    default_pricelist_id = fields.Many2one(
        'product.pricelist',
        string='Default pricelist for pricing',
        config_parameter='ateroo_base.pricelist.default',
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
        pricelist = IrConfigParameter.get_param('ateroo_base.pricelist.default')
        secret_key = IrConfigParameter.get_param('ateroo_base.secret.key')
        if product:
            res.update({'package_product_id': int(product)})
        if pricelist:
            res.update({'default_pricelist_id': int(pricelist)})
        if secret_key:
            res.update({'secret_key': secret_key})
        return res

    def set_values(self):
        super().set_values()
        IrConfigParameter = self.env['ir.config_parameter'].sudo()
        IrConfigParameter.set_param("ateroo_base.package.product", self.package_product_id.id)
        IrConfigParameter.set_param("ateroo_base.secret.key", self.secret_key)
        IrConfigParameter.set_param("ateroo_base.pricelist.default'", self.default_pricelist_id.id)
