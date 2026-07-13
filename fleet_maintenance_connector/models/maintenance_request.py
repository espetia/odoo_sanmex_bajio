# -*- coding: utf-8 -*-
import logging

from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError

_logger = logging.getLogger(__name__)


class MaintenanceRequest(models.Model):
    _inherit = "maintenance.request"

    vehicle_id = fields.Many2one(
        comodel_name="fleet.vehicle",
        compute="_compute_vehicle_id",
        store=True,
        string="Vehículo",
        help="Vehicle associated with this maintenance request.",
    )
    vehicle_kilometers = fields.Float(string="Kilómetros del vehículo", help="Kilómetros actuales del vehículo.")

    @api.depends("equipment_id")
    def _compute_vehicle_id(self):
        for record in self:
            if record.equipment_id.vehicle_id:
                record.vehicle_id = record.equipment_id.vehicle_id
            else:
                record.vehicle_id = False

    def _create_repair_order(self):
        """Create a repair order from the maintenance request."""
        if not self.vehicle_id:
            raise UserError(_("No hay vehiculo relacionado."))
        if not self.equipment_id:
            raise UserError(_("No hay equipo relacionado."))
        # if not self.equipment_id.id_maintenance_bom:
        #    raise UserError(_("No maintenance kit associated with the equipment: %s") % self.equipment_id.name)
        # if not self.equipment_id.id_maintenance_bom.bom_line_ids:
        #    raise UserError(
        #        _("The maintenance kit for equipment %s does not contain any products.") % self.equipment_id.name
        #    )
        # Create the repair order
        warehouse = False
        if self.company_id:
            warehouse = self.env["stock.warehouse"].search([("company_id", "=", self.company_id.id)], limit=1)
        repair_order = self.env["repair.order"].create(
            {
                "name": self.name,
                "product_id": self.category_id.product_id.id,
                "product_qty": 1.0,
                "product_uom": self.category_id.product_id.uom_po_id.id,
                "location_id": warehouse.lot_stock_id.id,
                "equipment_id": self.equipment_id.id,
                "description": self.name,
            }
        )
        # Link the repair order to the maintenance request
        if not repair_order:
            raise UserError(_("Fallo al crear la orden de reparación para la solicitud de mantenimiento"))

        if self.maintenance_type != "corrective":
            if not self.equipment_id.id_maintenance_bom:
                raise UserError(_("No hay kit de mantenimiento relacionado al equipo: %s") % self.equipment_id.name)
            if not self.equipment_id.id_maintenance_bom.bom_line_ids:
                raise UserError(_("El kit de mantenimiento %s no contiene productos.") % self.equipment_id.name)
            # crearte parts from the maintenance BOM
            parts_created = self._create_parts_from_bom(
                repair_order_id=repair_order.id,
                location_id=warehouse.lot_stock_id.id,
                bom=self.equipment_id.id_maintenance_bom,
            )
            if not parts_created:
                raise UserError(
                    _("Fallo al crear las partes desde el kit de mantenimiento para la orden de reparación.")
                )

        self.write(
            {
                "repair_order_id": repair_order.id,
                # "state": "in_repair",
            }
        )
        # Open the repair order form view
        return repair_order

    def action_create_repair_order(self):
        """Create a repair order from the maintenance request."""
        # if not self.vehicle_id:
        #    raise UserError(_("No hay vehiculo relacionado."))
        if not self.equipment_id:
            raise UserError(_("No hay equipo relacionado."))
        # if not self.equipment_id.id_maintenance_bom:
        #    raise UserError(_("No maintenance kit associated with the equipment: %s") % self.equipment_id.name)
        # if not self.equipment_id.id_maintenance_bom.bom_line_ids:
        #    raise UserError(
        #        _("The maintenance kit for equipment %s does not contain any products.") % self.equipment_id.name
        #    )
        # Create the repair order
        warehouse = False
        if self.company_id:
            warehouse = self.env["stock.warehouse"].search([("company_id", "=", self.company_id.id)], limit=1)
        repair_order = self.env["repair.order"].create(
            {
                "name": self.name,
                "product_id": self.category_id.product_id.id,
                "product_qty": 1.0,
                "product_uom": self.category_id.product_id.uom_po_id.id,
                "location_id": warehouse.lot_stock_id.id,
                "equipment_id": self.equipment_id.id,
                "description": self.name,
            }
        )
        # Link the repair order to the maintenance request
        if not repair_order:
            raise UserError(_("Fallo al crear la orden de reparación para la solicitud de mantenimiento."))

        if self.maintenance_type != "corrective":
            if not self.equipment_id.id_maintenance_bom:
                raise UserError(_("No hay kit de mantenimiento relacionado al equipo: %s") % self.equipment_id.name)
            if not self.equipment_id.id_maintenance_bom.bom_line_ids:
                raise UserError(_("El kit de mantenimiento %s no contiene productos.") % self.equipment_id.name)
            # crearte parts from the maintenance BOM
            parts_created = self._create_parts_from_bom(
                repair_order_id=repair_order.id,
                location_id=warehouse.lot_stock_id.id,
                bom=self.equipment_id.id_maintenance_bom,
            )
            if not parts_created:
                raise UserError(
                    _("Fallo al crear las partes desde el kit de mantenimiento para la orden de reparación.")
                )

        self.write(
            {
                "repair_order_id": repair_order.id,
                # "state": "in_repair",
            }
        )
        # Open the repair order form view
        return {
            "type": "ir.actions.act_window",
            "res_model": "repair.order",
            "res_id": repair_order.id,
            "view_mode": "form",
            "target": "current",
        }

    def _create_parts_from_bom(self, repair_order_id, location_id, bom=None):
        repair_order = self.env["repair.order"].browse(repair_order_id)
        if not repair_order.exists():
            raise ValueError(f"Orden de reparación {repair_order_id} no encontrada")
        """Create parts from the maintenance BOM."""
        if not self.equipment_id.id_maintenance_bom:
            raise UserError(_("No maintenance BOM associated with the equipment."))
        location_dest_id = self.env["stock.location"].search(
            [("usage", "=", "production"), ("company_id", "=", repair_order.company_id.id)], limit=1
        )
        if not location_dest_id:
            raise UserError(_("No production location found for the company: %s") % repair_order.company_id.name)

        for line in self.equipment_id.id_maintenance_bom.bom_line_ids:
            repair_line_vals = {
                "repair_id": repair_order.id,
                # "type": "add",
                "product_id": line.product_id.id,
                "name": line.product_id.display_name,
                "product_uom_qty": line.quantity,
                "product_uom": line.product_uom_id.id,
                "location_id": location_id,
                "location_dest_id": location_dest_id.id,
                "state": "draft",
                "company_id": repair_order.company_id.id,
                "price_unit": 0.0,
            }
            self.env["repair.line"].create(repair_line_vals)
        return True
