# -*- coding: utf-8 -*-
###########################################################################

from odoo import models, fields, api, _
from odoo.exceptions import UserError
import logging
_logger = logging.getLogger(__name__)

class AccountJournal(models.Model):
    _inherit = "account.journal"

    closing_fy = fields.Boolean(string="Para Póliza de Resultados")

    #@api.multi
    @api.constrains('closing_fy')    
    def _check_journal_closing_fy(self):
        if self.closing_fy and self.type != 'general':
            raise UserError(_('Advertencia !\nSolo puede marcar el Diario "Para Póliza de Resultados" si es de tipo "Misceláneo". Si tiene mas de uno marcado entonces se tomará el primero que haya sido registrado'))
        

        
class AccountCYEarningsBalanceTransfer(models.TransientModel):
    _inherit = "account.cy_earnings"

    #@api.multi
    def create_journal_entry(self):
        # Validaciones
        # anio1 = int(self.fiscalyear_origin.date_start[:4])
        # anio2 = int(self.fiscalyear_destiny.date_start[:4])
        # if not (anio1 < anio2 and (anio2-anio1) == 1):
        #     raise UserError(_('Advertencia !\nEl Año Fiscal Origen no es el Año anterior respecto al Año Fiscal Destino'))

        # Revisamos si ya existe una póliza previa        
        move_id = self.env['account.move'].search([('journal_id','=',self.journal_id.id),
                                                   ('closing_period','=',True),
                                                   ('current_year_earnings','=',True),
                                                   ('date','>=',self.period_id.date_start),
                                                   ('date','<=',self.period_id.date_stop)])

        if move_id:
            if move_id.state=='posted':
                move_id.button_cancel()
            move_id.unlink()
        # Listo !    
        if self.cy_earnings_account_id.user_type_id.with_context({'lang':'en_US'}).name != 'Current Year Earnings':
            raise UserError(_('Error !\nLa cuenta contable seleccionada no está configurada correctamente, debe ser cuenta de Tipo "Resultado del Ejercicio"'))
            
        period_id = self.env['account.period'].search([('fiscalyear_id','=',self.fiscalyear_id.id),('special','=',False)], order='name desc', limit=1)
        trialWizardObj = self.env['account.monthly_balance_wizard']        
        trial_balance_id = trialWizardObj.create({'chart_account_id': self.chart_account_id.id,
                                                 'company_id'       : self.env.user.company_id.id,
                                                 'period_id'        : period_id.id,
                                                 'partner_breakdown': True,
                                                 'output'           : 'list_view',})
        _logger.error('trial_balance_id: %s', trial_balance_id)
        balance_ids = eval(trial_balance_id.get_info()['domain'][1:-1])[2]
        _logger.error('balance_ids: %s', balance_ids)
        if not balance_ids:
            raise UserError(_('Advertencia !!!\nNo se pudo obtener los Saldos Finales del Periodo indicado.\nLa consulta no devolvió ningún registro'))
        
        journal_id = self.journal_id.id
        concept = self.entry_concept
        account_move = {
                        'ref'               : concept,
                        'item_concept'      : concept,
                        'journal_id'        : journal_id,
                        'narration'         : self.notes,
                        'date'              : self.period_id.date_start,
                        'current_year_earnings' : True,
                        'closing_period'    : True,
                        }
        
        move_lines = []
        current_year_earnings = 0.0
        for line in self.env['account.monthly_balance'].browse(balance_ids):
            _logger.error('balance_ids_line: %s', line)
            if line.account_id.internal_type in ('view','consolidation') or \
                line.account_id.user_type_id.with_context({'lang':'en_US'}).name not in ('Income', 'Other Income', 'Expenses', 'Direct Costs', 'Cost of Revenue'):
                continue
            if not line.ending_balance:
                continue                            
            """
            Tipos de Cuentas:
            - Receivable
            - Payable
            - Bank and Cash
            - Current Assets
            - Non-current Assets
            - Prepayments
            - Fixed Assets
            - Current Liabilities
            - Non-current Liabilities
            - Equity (Capital)
            - Current Year Earnings (Resultado del Ejercicio)
            - Other Income
            - Income
            - Depreciation
            - Expenses
            - Direct Costs (v9)  - Cost of Revenue (v10)
            """
            
            current_year_earnings += round((line.account_id.sing_1 > 0 and -line.ending_balance or line.ending_balance), 2)
            value = round((line.ending_balance * line.account_id.sing_1 * -1.0),2)

            move_line = (0,0, {
                                'name'          : concept,
                                'account_id'    : line.account_id.id,
                                'partner_id'    : line.partner_id and line.partner_id.id or False,
                                'debit'         : value >= 0 and value or 0.0,
                                'credit'        : value < 0 and abs(value) or 0.0,
                                'journal_id'    : journal_id,
                                })
            move_lines.append(move_line)
        move_line = (0,0, {
                            'name'          : _('Resultado del Ejercicio'),
                            'account_id'    : self.cy_earnings_account_id.id,
                            'partner_id'    : False,
                            'debit'         : current_year_earnings < 0 and abs(current_year_earnings) or 0.0,
                            'credit'        : current_year_earnings >= 0 and current_year_earnings or 0.0,
                            'journal_id'    : journal_id,
                            })
        move_lines.append(move_line)
        account_move.update({'line_ids': move_lines})
        move_id = self.env['account.move'].create(account_move)
        #res = self._cr.execute("""update account_move set period_id=%s where id=%s; 
        #                          update account_move_line set period_id=%s where move_id=%s;""" % 
        #                       (self.period_id.id, move_id.id,self.period_id.id, move_id.id))

        return {
                'domain'    : "[('id','='," + str(move_id.id) + ")]",
                'name'      : _('Póliza de Resultado del Ejercicio'),
                'view_mode' : 'tree,form',
                'view_type' : 'form',
                'res_model' : 'account.move',
                'type'      : 'ir.actions.act_window',
            }
        
        