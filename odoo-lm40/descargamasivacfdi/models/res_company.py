# -*- encoding: utf-8 -*-
from odoo import api, fields, models, _
import base64
import datetime
from datetime import date
import logging
_logger = logging.getLogger(__name__)
from odoo.exceptions import UserError, RedirectWarning, ValidationError


class res_company(models.Model):
    _inherit = 'res.company'


    certificate_file_FIEL = fields.Binary(string='Certificado (*.cer)', filters='*.cer,*.certificate,*.cert')
    certificate_key_file_FIEL = fields.Binary(string='Llave del Certificado (*.key)', filters='*.key')
    