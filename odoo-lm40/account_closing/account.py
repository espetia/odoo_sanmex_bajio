# -*- coding: utf-8 -*-
###########################################################################

from odoo import models, fields, api, _
from odoo.exceptions import UserError

        
class AccountMove(models.Model):
    _inherit = "account.move"
    
    current_year_earnings = fields.Boolean(string="Póliza de Resultados", default=False, readonly=True)
    

class AccountCYEarningsBalanceTransfer(models.TransientModel):
    _name = "account.cy_earnings"
    _description ="Wizard to Create Journal Entry for Opening Balance"

    company_id          = fields.Many2one('res.company', string="Compañía", required=True, readonly=True,
                                         default = lambda self: self.env.user.company_id)
    chart_account_id    = fields.Many2one('account.account', string='Plan Contable', required=True, 
                                        default=lambda self: self.env['account.account'].search([('parent_id','=',False), ('company_id','=',self.env.user.company_id.id)], limit=1))
    fiscalyear_id       = fields.Many2one('account.fiscal', string="Año Fiscal a Cerrar", required=True)
    journal_id          = fields.Many2one('account.journal', string="Diario Contable", required=True)
    period_id           = fields.Many2one('account.period', string="Periodo Destino", required=True)
    entry_concept       = fields.Char(string="Concepto Póliza")
    notes               = fields.Text(string="Notas")
    cy_earnings_account_id= fields.Many2one('account.account', string='Cuenta de Resultados', required=True, 
                                        default=lambda self: self.env['account.account'].with_context({'lang': 'en_US'}).search([('user_type_id.name','=','Current Year Earnings'),('company_id','=',self.env.user.company_id.id)], limit=1))
    

    @api.onchange('fiscalyear_id')
    def _onchange_fiscalyear_id(self):
        if not self.fiscalyear_id:
            return
        self.entry_concept = _("Póliza de Resultado del Ejercicio ") + self.fiscalyear_id.name
        for period in self.fiscalyear_id.period_ids.filtered(lambda r: r.special):
            self.period_id = period.id
