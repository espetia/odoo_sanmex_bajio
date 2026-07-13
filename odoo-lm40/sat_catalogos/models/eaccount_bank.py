# -*- encoding: utf-8 -*-

from odoo import api, fields, models, _
from odoo.exceptions import UserError, ValidationError
import logging
_logger = logging.getLogger(__name__)

class account_banks(models.Model):
    _name = 'eaccount.bank'
    
    name = fields.Char(string='Razón social', size=250, required=True, readonly=True)
    code = fields.Char(string='Nombre corto', size=250, required=True, readonly=True)
    bic  = fields.Char(string='Clave', size=11, required=True, readonly=True)

    @api.model
    def name_get(self):
        res = []
        for el in self:
            res.append((el.id, '[' + el.bic + '] ' + el.code))
        return res

    @api.model
    def name_search(self, name, args=None, operator='ilike', limit=20):
        args = args or []
        domain = []
        if not (name == '' and operator == 'ilike'):
            args += ['|', ('code', 'ilike', name), ('bic', 'ilike', name)]
        result = self.search(domain + args, limit=limit)
        res = result.name_get()
        return res


class res_bank_sat(models.Model):
    _inherit = 'res.bank'
    
    sat_bank_id = fields.Many2one('eaccount.bank', string='Código del SAT', ondelete="restrict")

    

 
