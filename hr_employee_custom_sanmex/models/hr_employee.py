# -*- coding: utf-8 -*-
import logging

from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError

_logger = logging.getLogger(__name__)


class HrEmployee(models.Model):
    _inherit = "hr.employee"

    curp_employee = fields.Char('CURP')
    nss_employee = fields.Char('NSS')
    rfc_employee = fields.Char('RFC')
