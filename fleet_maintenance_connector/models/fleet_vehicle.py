# -*- coding: utf-8 -*-
import logging

from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError

_logger = logging.getLogger(__name__)


class FleetVehicle(models.Model):
    _inherit = "fleet.vehicle"

    maintenance_state = fields.Selection(
        selection=[
            ("available", "Disponible"),
            ("maintenance_requested", "Solicitud de mantenimiento"),
            ("in_maintenance", "En mantenimiento"),
            ("maintenance_completed", "Mantenimiento completado"),
        ],
        string="Estado de mantenimiento",
        default="available",
        help="Estado del mantenimiento actual del vehículo. ",
        tracking=True,
    )
    maintenance_request_ids = fields.One2many(
        comodel_name="maintenance.request",
        inverse_name="vehicle_id",
        string="Solicitudes de mantenimiento",
        help="Lista de solicitudes de mantenimiento asociadas a este vehículo.",
    )
    maintenance_request_count = fields.Integer(
        string="Número de solicitudes de mantenimiento",
        compute="_compute_maintenance_request_count",
        help="Número total de solicitudes de mantenimiento asociadas a este vehículo.",
    )
    current_maintenance_request_id = fields.Many2one(
        comodel_name="maintenance.request",
        string="Solicitud de mantenimiento actual",
        compute="_compute_currennt_maintenance",
        help="Solicitud de mantenimiento actualmente activa para este vehículo.",
    )
    is_available_for_assignment = fields.Boolean(
        string="Disponible para asignación",
        compute="_compute_is_available_for_assignment",
        help="Indica si el vehículo está disponible para asignación a una solicitud de mantenimiento.",
    )
    next_maintenance_date = fields.Date(
        string="Próxima fecha de mantenimiento",
        help="Fecha programada para el próximo mantenimiento del vehículo.",
    )
    product_id = fields.Many2one(
        comodel_name="product.product",
        string="Producto asociado",
        help="Producto asociado al vehículo, utilizado para la gestión de materiales.",
    )
    id_maintenance_bom = fields.Many2one(
        "maintenance.bom",
        string="Kit de Mantenimiento",
        help="Kit de mantenimiento asociado a este vehiculo. "
        "Este kit se utilizará para el mantenimiento de este vehículo. "
        "El kit debe contener los productos necesarios para el mantenimiento.",
        domain="[('bom_line_ids', '!=', False)]",
    )

    @api.depends("maintenance_request_ids")
    def _compute_maintenance_request_count(self):
        for vehicle in self:
            vehicle.maintenance_request_count = len(vehicle.maintenance_request_ids)

    @api.depends("maintenance_request_ids", "maintenance_state")
    def _compute_currennt_maintenance(self):
        for record in self:
            current_requests = record.maintenance_request_ids.filtered(
                lambda r: r.stage_id.name in ["Nueva solicitud", "En progreso"]
            )
            record.current_maintenance_request_id = current_requests[0] if current_requests else False

    @api.depends("maintenance_state", "state_id")
    def _compute_is_available_for_assignment(self):
        for record in self:
            record.is_available_for_assignment = (
                record.maintenance_state == "available" and record.state_id.name not in ["Dañado", "Fuera de servicio"]
            )

    def _get_or_create_equipment(self):
        """Obtiene o crea el equipo correspondiente al vehículo"""
        equipment = self.env["maintenance.equipment"].search([("vehicle_id", "=", self.id)], limit=1)

        if not equipment:
            equipment = self.env["maintenance.equipment"].create(
                {
                    "name": self.name,
                    "vehicle_id": self.id,
                    "category_id": self._get_vehicle_category().id,
                    "id_maintenance_bom": self.id_maintenance_bom.id if self.id_maintenance_bom else False,
                }
            )

        return equipment.id

    def _get_vehicle_category(self):
        """Obtiene o crea la categoría de vehículos"""
        category = self.env["maintenance.equipment.category"].search([("name", "=", "Vehículos")], limit=1)

        if not category:
            category = self.env["maintenance.equipment.category"].create(
                {
                    "name": "Vehículos",
                }
            )

        return category

    def action_create_request_maintenance(self):
        """Crea una solicitud de mantenimiento para el vehículo"""
        # if not self.is_available_for_assignment:
        #    raise UserError(_("El vehículo no está disponible para asignación a una solicitud de mantenimiento."))

        equipment_id = self._get_or_create_equipment()

        request_vals = {
            "name": _("Solicitud de mantenimiento para %s") % self.name,
            "vehicle_id": self.id,
            "equipment_id": equipment_id,
            "maintenance_type": "corrective",
            "vehicle_kilometers": self.odometer,
            # "stage_id": self.env.ref("maintenance.stage_new").id,
        }

        request = self.env["maintenance.request"].create(request_vals)
        self.maintenance_request_ids += request
        # self.current_maintenance_request_id = request.id
        self.maintenance_state = "maintenance_requested"
        return {
            "type": "ir.actions.act_window",
            "res_model": "maintenance.request",
            "res_id": request.id,
            "view_mode": "form",
            "target": "current",
        }

    def action_view_maintenance_requests(self):
        """Abre la vista de solicitudes de mantenimiento asociadas al vehículo"""
        action = self.env["ir.actions.actions"]._for_xml_id("maintenance.hr_equipment_request_action")
        action["domain"] = [("vehicle_id", "=", self.id)]
        action["context"] = {"default_vehicle_id": self.id}
        return action