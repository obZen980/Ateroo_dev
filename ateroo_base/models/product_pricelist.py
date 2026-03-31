from odoo import models, fields, api, _
from odoo.tools import formatLang


class ProductPricelist(models.Model):
    _inherit = 'product.pricelist'

    orig_zone_id = fields.Many2one('delivery.tarif.zone', string='Origin zone')
    dest_zone_id = fields.Many2one('delivery.tarif.zone', string='Destination zone')


class ProductPricelistItem(models.Model):
    _inherit = 'product.pricelist.item'

    compute_price = fields.Selection(selection_add=[('range', 'Range')], ondelete={'range': 'cascade'})
    max_quantity = fields.Float(
        string="Max. Quantity",
        default=0,
        digits='Product Unit of Measure'
    )

    def _is_applicable_for(self, product, qty_in_product_uom):
        res = super()._is_applicable_for(product, qty_in_product_uom)
        if self.max_quantity and qty_in_product_uom > self.max_quantity:
            res = False
        return res

    def _compute_price(self, product, quantity, uom, date, currency=None):
        res = super()._compute_price(product, quantity, uom, date, currency)
        product_uom = product.uom_id
        if product_uom != uom:
            convert = lambda p: product_uom._compute_price(p, uom)
        else:
            convert = lambda p: p
        if self.compute_price == 'range':
            res = convert(self.fixed_price) / quantity
        return res

    @api.depends(
        'compute_price',
        'fixed_price',
        'pricelist_id',
        'percent_price',
        'price_discount',
        'price_markup',
        'price_surcharge',
        'base',
        'base_pricelist_id',
    )
    def _compute_price_label(self):
        super()._compute_price_label()
        for item in self:
            if item.compute_price == 'range':
                item.price = formatLang(
                    item.env,
                    item.fixed_price,
                    dp="Product Price",
                    currency_obj=item.currency_id
                )
