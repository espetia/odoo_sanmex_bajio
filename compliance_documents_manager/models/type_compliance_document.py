# -*- coding: utf-8 -*-
import logging

from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError

_logger = logging.getLogger(__name__)


class TypeComplianceDocument(models.Model):
    _name = 'type.compliance.document'
    _description = 'Tipo de documento'

    name = fields.Char('Nombre', required=True, )
    description = fields.Text('Descripción')
    active = fields.Boolean('Activo', default=True)
    type_resource = fields.Selection(
        [
            ("empleado", "Empleado"),
            ("propiedad", "Propiedad"),
        ],
        string="Tipo de recurso",
        required=True,
    )
