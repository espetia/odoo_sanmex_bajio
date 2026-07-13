# -*- coding: utf-8 -*-
import logging

from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError

_logger = logging.getLogger(__name__)


class MaintenanceBom(models.Model):
    _name = "maintenance.bom"
    _description = "MaintenanceBom"

    name = fields.Char("Nombre de Kit", required=True)
    bom_line_ids = fields.One2many(
        "maintenance.bom.line",
        "bom_id",
        string="Líneas de Kit",
        help="Lista de productos que componen el kit de mantenimiento",
    )
    partner_id = fields.Many2one("res.partner", string="Proveedor", help="Proveedor del kit de mantenimiento")
    account_analytic_id = fields.Many2one(
        "account.analytic.account",
        string="Cuenta Analítica",
        help="Cuenta analítica asociada al kit de mantenimiento",
    )


class MaintenanceBomLine(models.Model):
    _name = "maintenance.bom.line"
    _description = "MaintenanceBomLine"

    bom_id = fields.Many2one("maintenance.bom", string="Kit", required=True)
    product_id = fields.Many2one("product.product", string="Producto", required=True)
    product_tmpl_id = fields.Many2one(
        "product.template",
        string="Plantilla de Producto",
        related="product_id.product_tmpl_id",
        store=True,
        readonly=True,
    )
    product_uom_id = fields.Many2one("uom.uom", string="Unidad de Medida", required=True)
    quantity = fields.Float(string="Cantidad", required=True, default=1.0)

    @api.constrains("quantity")
    def _check_quantity(self):
        for line in self:
            if line.quantity <= 0:
                raise ValidationError(_("La cantidad debe ser mayor que cero."))

    @api.onchange("product_id")
    def _onchange_product_id(self):
        for line in self:
            if line.product_id:
                line.product_uom_id = line.product_id.uom_po_id
            else:
                line.product_uom_id = False
