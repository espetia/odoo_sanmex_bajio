# -*- coding: utf-8 -*-
import logging

from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError
from odoo.osv import expression

_logger = logging.getLogger(__name__)


class ResPartner(models.Model):
    _inherit = 'res.partner'

    trade_name = fields.Char('Nombre comercial')

    @api.model
    def _name_search(self, name, args=None, operator='ilike', limit=100, name_get_uid=None):
        args = args or []
        domain = []
        if name:
            args += ['|', '|', ('name', operator, name), ('email', operator, name),('trade_name', operator,name)]
        return self._search(args, limit=limit, access_rights_uid=name_get_uid)