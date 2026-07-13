# -*- coding: utf-8 -*-
import logging

from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError

_logger = logging.getLogger(__name__)


class StockLotLog(models.Model):
    _name = 'stock.lot.log'
    _description = 'Log de movimientos de stock'

    name = fields.Char('Name')
    lot_id = fields.Many2one('stock.productio.lot', string='Lote')
    product_id = fields.Many2one('product.product', string='Producto')
    date_change = fields.Datetime(
        string=_('Fecha'),
        default=fields.Datetime.now,
    )
    stage_id_new = fields.Many2one('stock.stage.product', string='Etapa Nueva')
    stage_id_old = fields.Many2one('stock.stage.product', string='Etapa anterior')