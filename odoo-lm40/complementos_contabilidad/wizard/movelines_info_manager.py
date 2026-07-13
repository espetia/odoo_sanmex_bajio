# -*- encoding: utf-8 -*-
#

from odoo import api, fields, models, _
from odoo.exceptions import UserError, ValidationError

class moveline_info_manager(models.TransientModel):
    _name = 'moveline.info.manager'
    
    line_id         = fields.Many2one('account.move.line', string='Partida Contable')#, required=True)
    line_name       = fields.Char(string='Nombre', related='line_id.name', readonly=True)
    line_account    = fields.Many2one('account.account', related='line_id.account_id', string='Cuenta', readonly=True)
    debit           = fields.Monetary(string='Debe', related='line_id.debit', readonly=True, currency_field='currency_id')
    credit          = fields.Monetary(string='Haber', related='line_id.credit', readonly=True, currency_field='currency_id')
    complement_ids  = fields.One2many('eaccount.complements', related='line_id.complement_line_ids', string='Complementos')
    currency_id     = fields.Many2one('res.currency', string='Moneda', required=True, default=lambda self: self.env.user.company_id.currency_id)

    
    @api.model
    def save_changes(self):
        return {'type': 'ir.actions.act_window_close'}





