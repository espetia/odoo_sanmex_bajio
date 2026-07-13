# -*- coding: utf-8 -*-
import logging

from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError

_logger = logging.getLogger(__name__)


class PurchaseOrder(models.Model):
    _inherit = 'purchase.order'

    repair_order_id = fields.Many2one(
        'repair.order',
        string='Orden de Reparación',
        readonly=True
    )