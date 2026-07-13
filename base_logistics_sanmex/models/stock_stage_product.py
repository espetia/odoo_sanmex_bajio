# -*- coding: utf-8 -*-
import logging

from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError

_logger = logging.getLogger(__name__)


class StockStageProduct(models.Model):
    _name = 'stock.stage.product'
    _description = 'Etapas de bodega'
    _order = 'sequence,name'

    name = fields.Char('Nombre')
    sequence = fields.Integer('Secuencia Kanban')
    fold = fields.Boolean('Desplegado en Kanban', help="This stage is folded in the kanban view.")
