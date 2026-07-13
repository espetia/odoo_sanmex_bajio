# -*- coding: utf-8 -*-
import logging

from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError

_logger = logging.getLogger(__name__)


class FleetVehicleOdometer(models.Model):
    _inherit = "fleet.vehicle.odometer"

    batch_id = fields.Many2one(
        "fleet.batch.odometer", string="Batch", help="Batch of odometers this record belongs to"
    )
