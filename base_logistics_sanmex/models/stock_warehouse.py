# -*- coding: utf-8 -*-
import logging

from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError

_logger = logging.getLogger(__name__)


class StockWarehouse(models.Model):
    _inherit = 'stock.warehouse'

    product_sanitary = fields.Many2one('product.product', string='Producto Sanitario', help="Producto usado para hacer los movimientos de las rentas de los baños con inventario", domain="[('is_resource_sanitary', '=', True)]")
    user_id = fields.Many2one('res.users', string='Personal de Logistica')
