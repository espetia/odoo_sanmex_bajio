# -*- coding: utf-8 -*-
import logging

from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError

_logger = logging.getLogger(__name__)


class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    product_sanitary = fields.Many2one('product.product', string='Producto Sanitario', help="Producto usado para hacer los movimientos de las rentas de los baños con inventario",domain="[('is_resource_sanitary', '=', True)]", config_parameter='base_logistics_sanmex.default_product_sanitary',)


    def set_values(self):
        super(ResConfigSettings, self).set_values()
        #self.env['ir.config_parameter'].set_param(
        #    'base_logistics_sanmex.product_sanitary', self.product_sanitary.id)

    # @api.model
    # def get_values(self):
    #     res = super(ResConfigSettings, self).get_values()
    #     params = self.env['ir.config_parameter'].sudo()
    #     res.update(
    #         product_sanitary=params.get_param('base_logistics_sanmex.product_sanitary')
    #     )
    #     return res