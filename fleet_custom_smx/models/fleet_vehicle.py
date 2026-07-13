# -*- coding: utf-8 -*-
import logging

from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError

_logger = logging.getLogger(__name__)


class FleetVehicle(models.Model):
    _inherit = 'fleet.vehicle'

    odometer_line_batch_ids = fields.One2many(
        'fleet.batch.odometer.line', 'vehicle_id', string='Lineas de carga',
        help='Records of odometer readings associated with fuel entries.'
    )
    odometer_line_batch_count = fields.Integer(
        string='Número de líneas de odómetro',
        compute='_compute_odometer_line_count'
    )

    @api.depends('odometer_line_batch_ids')
    def _compute_odometer_line_count(self):
        for vehicle in self:
            vehicle.odometer_line_batch_count = len(vehicle.odometer_line_batch_ids)

    def action_view_odometer_batch(self):
        self.ensure_one()
        action = self.env["ir.actions.actions"]._for_xml_id("fleet_custom_smx.action_fleet_batch_odometer_line")
        action["domain"] = [("vehicle_id", "=", self.id)]
        action["context"] = {"default_vehicle_id": self.id}
        return action