# -*- coding: utf-8 -*-
import logging

from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError

_logger = logging.getLogger(__name__)


class MaintenanceEquipmentCategory(models.Model):
    _inherit = "maintenance.equipment.category"

    product_id = fields.Many2one(
        comodel_name="product.product",
        string="Producto reparación",
        help="Producto asociado a la categoría de equipo, utilizado para la gestión de reparaciones.",
    )
