# -*- coding: utf-8 -*-
import logging

from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError

_logger = logging.getLogger(__name__)


class RepairToPurchaseWizard(models.TransientModel):
    _name = "repair.to.purchase.wizard"
    _description = _("Wizard para crear OC desde Reparación")

    repair_order_id = fields.Many2one("repair.order", string="Orden de Reparación", required=True)
    partner_id = fields.Many2one(
        "res.partner", string="Proveedor", required=True, domain=[("is_company", "=", True), ("supplier_rank", ">", 0)]
    )
    line_ids = fields.One2many("repair.to.purchase.wizard.line", "wizard_id", string="Líneas de Productos")
    group_by_supplier = fields.Boolean(
        string="Agrupar por Proveedor", default=True, help="Crear una OC por cada proveedor diferente"
    )

    @api.onchange("repair_order_id")
    def _onchange_repair_order_id(self):
        if self.repair_order_id:
            lines = []
            for operation in self.repair_order_id.operations:
                if operation.product_id:
                    # if operation.product_id and operation.product_id.type == "product":
                    # Buscar proveedor preferido del producto
                    supplier = False
                    if operation.product_id.seller_ids:
                        supplier = operation.product_id.seller_ids[0].name

                    lines.append(
                        (
                            0,
                            0,
                            {
                                "product_id": operation.product_id.id,
                                "product_qty": operation.product_uom_qty,
                                "product_uom": operation.product_uom.id,
                                "price_unit": operation.price_unit,
                                "selected": True,
                                "supplier_id": supplier.id if supplier else False,
                                "repair_line_id": operation.id,
                            },
                        )
                    )
            self.line_ids = lines

    def action_create_purchase_order(self):
        """Crear órdenes de compra"""
        if not self.line_ids.filtered("selected"):
            raise UserError(_("Debe seleccionar al menos una línea."))

        selected_lines = self.line_ids.filtered("selected")

        if self.group_by_supplier:
            # Agrupar por proveedor
            suppliers = {}
            for line in selected_lines:
                supplier_id = line.supplier_id.id if line.supplier_id else self.partner_id.id
                if supplier_id not in suppliers:
                    suppliers[supplier_id] = []
                suppliers[supplier_id].append(line)

            purchase_orders = []
            for supplier_id, lines in suppliers.items():
                supplier = self.env["res.partner"].browse(supplier_id)
                po = self._create_purchase_order(supplier, lines)
                purchase_orders.append(po)
        else:
            # Una sola OC con el proveedor seleccionado
            po = self._create_purchase_order(self.partner_id, selected_lines)
            purchase_orders = [po]

        # Retornar acción para ver las OC creadas
        if len(purchase_orders) == 1:
            return {
                "name": _("Orden de Compra Creada"),
                "type": "ir.actions.act_window",
                "res_model": "purchase.order",
                "res_id": purchase_orders[0].id,
                "view_mode": "form",
                "target": "current",
            }
        else:
            return {
                "name": _("Órdenes de Compra Creadas"),
                "type": "ir.actions.act_window",
                "res_model": "purchase.order",
                "view_mode": "tree,form",
                "domain": [("id", "in", [po.id for po in purchase_orders])],
            }

    def _create_purchase_order(self, partner, lines):
        """Crear una orden de compra"""
        po_vals = {
            "partner_id": partner.id,
            "repair_order_id": self.repair_order_id.id,
            "origin": self.repair_order_id.name,
            "order_line": [],
        }
        vehicle = self.repair_order_id.equipment_id.vehicle_id
        for line in lines:
            po_line_vals = {
                "product_id": line.product_id.id,
                "name": line.product_id.display_name,
                "product_qty": line.product_qty,
                "product_uom": line.product_uom.id,
                "price_unit": line.price_unit,
                "date_planned": fields.Datetime.now(),
            }
            if vehicle:
                po_line_vals["vehicle_id"] = vehicle.id
            po_vals["order_line"].append((0, 0, po_line_vals))

        return self.env["purchase.order"].create(po_vals)


class RepairToPurchaseWizardLine(models.TransientModel):
    _name = "repair.to.purchase.wizard.line"
    _description = _("Línea del Wizard de Reparación a Compra")

    wizard_id = fields.Many2one("repair.to.purchase.wizard", required=True)
    product_id = fields.Many2one("product.product", string="Producto", required=True)
    product_qty = fields.Float(string="Cantidad", required=True)
    product_uom = fields.Many2one("uom.uom", string="Unidad de Medida")
    price_unit = fields.Float(string="Precio Unitario")
    selected = fields.Boolean(string="Seleccionar", default=True)
    supplier_id = fields.Many2one("res.partner", string="Proveedor Sugerido")
    repair_line_id = fields.Many2one("repair.line", string="Línea de Reparación")
