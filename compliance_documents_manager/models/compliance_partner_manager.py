# -*- coding: utf-8 -*-
import logging

from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError

_logger = logging.getLogger(__name__)


class CompliancePartnerManager(models.Model):
    _name = "compliance.partner.manager"
    _description = "Registro de proveedores"

    name = fields.Char("Nombre")
    partner_id = fields.Many2one("res.partner", string="Proveedor")
    line_ids = fields.One2many(
        "compliance.partner.manager.line", "compliance_partner_manager_id", string="Tramites de proveedores"
    )


class CompliancePartnerManagerLine(models.Model):
    _name = "compliance.partner.manager.line"
    _description = "Línea de tramites de proveedores"

    name = fields.Char("Nombre")
    compliance_partner_manager_id = fields.Many2one("compliance.partner.manager", string="Registro de proveedores")
    type_document = fields.Selection(
        [
            ("insurance", "Seguro"),
            ("license", "Licencia"),
            ("permit", "Permiso"),
            ("other", "Otro"),
        ],
        string="Tipo de documento",
        required=True,
    )
    type_resource = fields.Selection(
        [
            ("vehicle", "Vehículo"),
            ("employee", "Empleado"),
            ("property", "Propiedad"),
            ("other", "Otro"),
        ],
        string="Tipo de recurso",
        required=True,
    )
