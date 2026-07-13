# -*- coding: utf-8 -*-
import logging

from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError

_logger = logging.getLogger(__name__)


class FleetVehicle(models.Model):
    _inherit = "fleet.vehicle"

    n_economic = fields.Char(
        string="Número económico",
        help="Número económico del vehículo, utilizado para identificarlo dentro de la empresa.",
    )

    @api.depends("model_id.brand_id.name", "model_id.name", "license_plate", "n_economic")
    def _compute_vehicle_name(self):
        for record in self:
            base_name = (
                (record.model_id.brand_id.name or "")
                + "/"
                + (record.model_id.name or "")
                + "/"
                + (record.license_plate or _("No Plate"))
            )

            if record.n_economic:
                record.name = record.n_economic + "/" + base_name
            else:
                record.name = base_name
