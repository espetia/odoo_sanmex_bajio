# -*- coding: utf-8 -*-
import logging

from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError

_logger = logging.getLogger(__name__)


class MaintenanceEquipment(models.Model):
    _inherit = "maintenance.equipment"

    vehicle_id = fields.Many2one(
        comodel_name="fleet.vehicle",
        string="Vehículo",
    )
    id_maintenance_bom = fields.Many2one(
        "maintenance.bom",
        string="Kit de Mantenimiento",
        help="Kit de mantenimiento asociado a este equipo. "
        "Este kit se utilizará para el mantenimiento de este equipo. "
        "El kit debe contener los productos necesarios para el mantenimiento.",
        domain="[('bom_line_ids', '!=', False)]",
    )
