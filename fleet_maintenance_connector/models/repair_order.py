# -*- coding: utf-8 -*-
import logging

from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError

_logger = logging.getLogger(__name__)


class RepairOrder(models.Model):
    _inherit = "repair.order"

    equipment_id = fields.Many2one(
        comodel_name="maintenance.equipment",
        string="Equipo de Mantenimiento",
        help="Equipo de mantenimiento asociado a esta orden de reparación.",
    )
    purchase_order_ids = fields.One2many("purchase.order", "repair_order_id", string="Órdenes de Compra Relacionadas")
    purchase_count = fields.Integer(string="Cantidad de OC", compute="_compute_purchase_count")
    purchase_states_summary = fields.Char(
        string="Estados de Órdenes de Compra", compute="_compute_purchase_states_summary", store=True
    )

    @api.depends("purchase_order_ids.state")
    def _compute_purchase_states_summary(self):
        """Genera un resumen de los estados de las órdenes de compra"""
        for record in self:
            if not record.purchase_order_ids:
                record.purchase_states_summary = "Sin órdenes de compra"
            else:
                state_mapping = {
                    "draft": "Borrador",
                    "sent": "Enviado",
                    "to approve": "Por Aprobar",
                    "purchase": "Orden de Compra",
                    "done": "Completado",
                    "cancel": "Cancelado",
                }

                states = record.purchase_order_ids.mapped("state")
                state_counts = {}

                for state in states:
                    state_name = state_mapping.get(state, state.title())
                    state_counts[state_name] = state_counts.get(state_name, 0) + 1

                summary_parts = []
                for state_name, count in state_counts.items():
                    if count > 1:
                        summary_parts.append(f"{count} {state_name}")
                    else:
                        summary_parts.append(state_name)

                record.purchase_states_summary = ", ".join(summary_parts)

    @api.depends("purchase_order_ids")
    def _compute_purchase_count(self):
        for record in self:
            record.purchase_count = len(record.purchase_order_ids)

    def action_create_purchase_order(self):
        """Abrir wizard para crear orden de compra"""
        if not self.operations:
            raise UserError(_("No hay partes en esta orden de reparación."))

        return {
            "name": _("Crear Orden de Compra"),
            "type": "ir.actions.act_window",
            "res_model": "repair.to.purchase.wizard",
            "view_mode": "form",
            "target": "new",
            "context": {
                "default_repair_order_id": self.id,
                "default_partner_id": self.partner_id.id,
            },
        }

    def action_view_purchase_orders(self):
        """Ver órdenes de compra relacionadas"""
        return {
            "name": _("Órdenes de Compra"),
            "type": "ir.actions.act_window",
            "res_model": "purchase.order",
            "view_mode": "tree,form",
            "domain": [("repair_order_id", "=", self.id)],
            "context": {"create": False},
        }

    def action_create_order_from_kit(self):
        """Crear órdenes de compra desde kits de mantenimiento"""
        for order in self:
            if not order.equipment_id or not order.equipment_id.id_maintenance_bom:
                continue

            bom = order.equipment_id.id_maintenance_bom
            if not bom.bom_line_ids:
                continue

            po_vals = {
                "partner_id": bom.partner_id.id if bom.partner_id else order.partner_id.id,
                "repair_order_id": order.id,
                "origin": order.name,
                "project_id": bom.account_analytic_id.id if bom.account_analytic_id else False,
                "order_line": [],
            }
            vehicle = order.equipment_id.vehicle_id
            for line in order.operations:
                po_line_vals = {
                    "product_id": line.product_id.id,
                    "name": line.product_id.display_name,
                    "product_qty": line.product_uom_qty,
                    "product_uom": line.product_uom.id,
                    "price_unit": line.product_id.standard_price,
                    "date_planned": fields.Datetime.now(),
                }
                if vehicle:
                    po_line_vals["vehicle_id"] = vehicle.id
                po_vals["order_line"].append((0, 0, po_line_vals))

            purchase_order = self.env["purchase.order"].sudo().create(po_vals)
            purchase_order.write({"project_id": bom.account_analytic_id.id if bom.account_analytic_id else False})
            return purchase_order
