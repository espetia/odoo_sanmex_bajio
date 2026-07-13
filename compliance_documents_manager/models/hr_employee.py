# -*- coding: utf-8 -*-
import logging

from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError

_logger = logging.getLogger(__name__)


class HrEmployee(models.Model):
    _inherit = "hr.employee"

    is_operative = fields.Boolean(
        string="Operativo",
        help="Empleado es operativo",
        default=False,
    )
    compliance_document_ids = fields.One2many(
        comodel_name="compliance.document.line",
        inverse_name="employee_id",
        string="Documentos",
        help="Lista de documentos asociados al empleado.",
    )
