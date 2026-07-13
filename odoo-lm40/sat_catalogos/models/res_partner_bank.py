# -*- encoding: utf-8 -*-
from odoo import api, fields, models, _


class res_partner_bank(models.Model):
    _inherit = 'res.partner.bank'

    @api.model
    def _get_take_digits(self):        
        self.last_acc_number = self.acc_number and len(self.acc_number) >=4 and self.acc_number[-4:] or False
        
    clabe           = fields.Char(string='Clabe Interbancaria', size=64, required=False)
    last_acc_number = fields.Char(compute='_get_take_digits', string="Ultimos 4 digitos")
    currency2_id    = fields.Many2one('res.currency', string='Currency2')
    reference       = fields.Char(string='Reference', size=64, help='Reference used in this bank')
