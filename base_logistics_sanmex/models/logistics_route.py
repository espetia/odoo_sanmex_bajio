# -*- coding: utf-8 -*-
import logging

from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError

_logger = logging.getLogger(__name__)


class LogisticsRoute(models.Model):
    _name = 'logistics.route'
    _description = _('Logistica Rutas')

    name = fields.Char(_('Name'))
    code = fields.Char('Código')
    stock_house_id = fields.Many2one('stock.warehouse', string='Almacén')