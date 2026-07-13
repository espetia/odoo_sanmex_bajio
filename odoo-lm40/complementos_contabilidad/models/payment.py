# -*- encoding: utf-8 -*-
#


from odoo import models, fields, api, _
from odoo.exceptions import UserError
from odoo.exceptions import UserError, RedirectWarning, ValidationError
import logging
_logger = logging.getLogger(__name__)

class payment_fit_wizard(models.TransientModel):
    _inherit = "account.payment.register"
    
    partner_acc_id  = fields.Many2one('res.partner.bank', string='Cuenta Bancaria')
    partner_parent_id = fields.Many2one('res.partner', related='partner_id.parent_id', string='Parent Partner')
    cmpl_type       = fields.Selection([('check', 'Cheque'), 
                                        ('transfer', 'Transferencia'), 
                                        ('payment', 'Otro método de pago')], 
                                       string='Tipo de complemento', 
                                       help='Indique el tipo de complemento a usar para este pago.')
    other_payment   = fields.Many2one('eaccount.payment.methods', string='Método de Pago SAT')
    partner_id = fields.Many2one('res.partner', string='Partner')
    
    def get_payment_vals(self):
        res = super(payment_fit_wizard, self).get_payment_vals()
        res.update({
            'cmpl_type'     : self.cmpl_type,
            'partner_acc_id': self.partner_acc_id.id,
            })
        return res
    
    

class payment_fit(models.Model):
    _inherit = 'account.payment'
    
    partner_parent_id = fields.Many2one('res.partner', related='partner_id.parent_id', string='Parent Partner')
    partner_acc_id  = fields.Many2one('res.partner.bank', string='Cuenta Bancaria', readonly=True, states={'draft': [('readonly', False)]})
    cmpl_type       = fields.Selection([('check', 'Cheque'), 
                                        ('transfer', 'Transferencia'), 
                                        ('payment', 'Otro método de pago')], 
                                       string='Tipo de complemento', 
                                       readonly=True, states={'draft': [('readonly', False)]},
                                       help='Indique el tipo de complemento a usar para este pago.')
    other_payment   = fields.Many2one('eaccount.payment.methods', string='Método de Pago SAT', readonly=True, states={'draft': [('readonly', False)]})

    """@api.onchange('journal_id')
    def _onchange_journal(self):
        res = super(payment_fit,self)._onchange_journal()
        if self.journal_id:
            self.cmpl_type = self.journal_id.cmlp_type_id or False
            self.other_payment = self.journal_id.payment_method_id or False
            if self.journal_id.cmlp_type_id != 'check':
                self.check_number = False
        return res"""
        
    
    @api.model
    def _create_payment_entry(self, amount):
        move = super(payment_fit, self)._create_payment_entry(amount)
        company = self.env.user.company_id
        if not company.auto_mode_enabled:
            return move
        cmplObj = self.env['eaccount.complements']
        cmplTypeObj = self.env['eaccount.complement.types']
        for payment in self:
            if not payment.cmpl_type:
                continue
            
            ## Obtenemos los valores base
            ## Inicio
            # Obtenemos la partida sobre la cual registrar el complemento
            line_id = [ ln for ln in payment.move_line_ids if ln.account_id.internal_type == 'liquidity' ]
            
            if not line_id:
                raise ValidationError (_("Error!\nEste diario no deberia generar Complementos de Pago, debido a que no existe una cuenta de Tipo Liquidez."))

            cmpl_vals = {
                 'compl_currency_id': payment.currency_id.id,
                 'amount'           : payment.amount,
                 'compl_date'       : payment.payment_date,
                 'type_id'          : cmplTypeObj.search([('key', '=', payment.cmpl_type)])[0].id,
                 'type_key'         : payment.cmpl_type
                }
            curr_rate = 1.0
            rate_lines = [ rate for rate in payment.currency_id.rate_ids if rate.name[0:10] == payment.payment_date ]
            if len(rate_lines) and rate_lines[0].rate:
                curr_rate = 1 / rate_lines[0].rate
            else:
                rate_lines = [{'name':val.name,'rate':val.rate} for val in payment.currency_id.rate_ids]
                _logger.info("rate_lines: %s" % rate_lines)
                
                rate_lines = sorted(rate_lines, key=lambda a: a['name'], reverse=True)
                for ln in rate_lines:
                    if ln['name'] < payment.payment_date and ln['rate']:
                        curr_rate = 1 / ln['rate']
                        break
            cmpl_vals['exchange_rate'] = curr_rate
            if cmpl_vals['type_key'] == 'check':
                cmpl_vals['check_number'] = payment.check_number or payment.journal_id.check_next_number
            if cmpl_vals['type_key'] == 'payment':
                cmpl_vals['pay_method_id'] = payment.other_payment.id or payment.journal_id.other_payment.id
                
            cmpl_vals['move_line_id'] = line_id[0].id
            # Fin
            # Validaciones generales
            
            ## Cobros a Clientes y/o Devoluciones de Proveedores
            if payment.payment_type == 'inbound':
                if payment.cmpl_type in ('transfer','check'): # Se requieren TODOS los datos para el complemento
                    # Beneficiario
                    cmpl_vals['payee_id'] = company.partner_id.id 
                    # Datos Emisor
                    cmpl_vals['rfc'] = payment.partner_id.rfc
                    cmpl_vals['show_native_accs'] = True
                    if payment.cmpl_type == 'transfer' or (payment.cmpl_type == 'check' and payment.partner_acc_id):
                        cmpl_vals['origin_native_accid'] = payment.partner_acc_id.id
                        origin_bank = payment.partner_acc_id and payment.partner_acc_id.bank_id
                        cmpl_vals['origin_bank_id'] = origin_bank.id
                        cmpl_vals['origin_bank_key'] = origin_bank.sat_bank_id.bic
                        if origin_bank.sat_bank_id.bic == '999':
                            cmpl_vals['origin_frgn_bank'] = origin_bank.name
                
                    # Datos Receptor
                    cmpl_vals['rfc2'] = company.rfc
                    cmpl_vals['destiny_account_id'] = payment.journal_id.account_credit_id.id
                    destiny_bank = payment.journal_id.account_debit_id.bank_id
                    cmpl_vals['destiny_bank_id'] = destiny_bank.id
                    cmpl_vals['destiny_bank_key'] = destiny_bank.sat_bank_id.bic
                    if destiny_bank.sat_bank_id.bic == '999':
                        cmpl_vals['destiny_frgn_bank'] = destiny_bank.name
                
                elif payment.cmpl_type == 'payment':
                    # Beneficiario
                    cmpl_vals['payee_id'] = company.partner_id.id 
                    # Datos Emisor
                    cmpl_vals['rfc'] = payment.partner_id.rfc
                    cmpl_vals['show_native_accs'] = True
                    
                
                    # Datos Receptor
                    cmpl_vals['rfc2'] = company.rfc
                    if payment.journal_id.account_credit_id:
                        cmpl_vals['destiny_account_id'] = payment.journal_id.account_credit_id.id
                        destiny_bank = payment.journal_id.account_debit_id.bank_id
                        cmpl_vals['destiny_bank_id'] = destiny_bank.id
                        cmpl_vals['destiny_bank_key'] = destiny_bank.sat_bank_id.bic
                        if destiny_bank.sat_bank_id.bic == '999':
                            cmpl_vals['destiny_frgn_bank'] = destiny_bank.name                    
            
            ## Pagos a Proveedores y/o Devoluciones a Clientes
            elif payment.payment_type == 'outbound':
                if payment.cmpl_type in ('transfer','check'): # Se requieren TODOS los datos para el complemento
                    # Beneficiario
                    cmpl_vals['payee_id'] = payment.partner_id.id 
                    # Datos Emisor
                    cmpl_vals['rfc'] = company.rfc
                    cmpl_vals['origin_account_id'] = payment.journal_id.account_credit_id.id
                    origin_bank = payment.journal_id.account_credit_id.bank_id
                    cmpl_vals['origin_bank_id'] = origin_bank.id
                    cmpl_vals['origin_bank_key'] = origin_bank.sat_bank_id.bic
                    if origin_bank.sat_bank_id.bic == '999':
                        cmpl_vals['origin_frgn_bank'] = origin_bank.name                    
                    # Datos Receptor
                    cmpl_vals['rfc2'] = payment.partner_id.rfc and payment.partner_id.rfc or ''
                    cmpl_vals['destiny_native_accid'] = payment.partner_acc_id.id
                    cmpl_vals['show_native_accs1'] = True
                    destiny_bank = payment.partner_acc_id.bank_id
                    cmpl_vals['destiny_bank_id'] = destiny_bank.id
                    cmpl_vals['destiny_bank_key'] = destiny_bank.sat_bank_id.bic
                    if destiny_bank.sat_bank_id.bic == '999':
                        cmpl_vals['destiny_frgn_bank'] = destiny_bank.name
            
            
                elif payment.cmpl_type == 'payment': 
                    # Beneficiario
                    cmpl_vals['payee_id'] = payment.partner_id.id 
                    # Datos Emisor
                    cmpl_vals['rfc'] = company.rfc
                    
                    
                    # Datos Receptor
                    cmpl_vals['rfc2'] = payment.partner_id.rfc
                    if payment.partner_acc_id:
                        cmpl_vals['destiny_native_accid'] = payment.partner_acc_id.id
                        cmpl_vals['show_native_accs1'] = True
                        destiny_bank = payment.partner_acc_id.bank_id
                        cmpl_vals['destiny_bank_id'] = destiny_bank.id
                        cmpl_vals['destiny_bank_key'] = destiny_bank.sat_bank_id.bic
                        if destiny_bank.sat_bank_id.bic == '999':
                            cmpl_vals['destiny_frgn_bank'] = destiny_bank.name                
            
            ## Transferencias entre cuentas propias
            elif payment.payment_type == 'transfer':
                cmpl_vals['payee_id'] = company.partner_id.id
                cmpl_vals['rfc'] = company.rfc
                cmpl_vals['rfc2'] = company.rfc
                if payment.cmpl_type in ('transfer','check'):
                    # Datos Emisor
                    cmpl_vals['origin_account_id'] = payment.journal_id.account_credit_id.id
                    origin_bank = payment.journal_id.account_credit_id.bank_id
                    cmpl_vals['origin_bank_id'] = origin_bank.id
                    cmpl_vals['origin_bank_key'] = origin_bank.sat_bank_id.bic
                    if origin_bank.sat_bank_id.bic == '999':
                        cmpl_vals['origin_frgn_bank'] = origin_bank.name
            
                if payment.destination_journal_id.cmlp_type_id in ('transfer','check'):
                    # Datos destino
                    cmpl_vals['destiny_bank_id'] = payment.destination_journal_id.account_debit_id.bank_id.id
                    cmpl_vals['destiny_account_id'] = payment.destination_journal_id.account_debit_id.id
                    cmpl_vals['show_native_accs1'] = False                    
            
            cmplObj.create(cmpl_vals)
            resp = payment.move_line_ids[0].move_id.write({'item_concept': self.company_id._assembly_concept(payment.payment_type, voucher=payment)})
            #_logger.error('concepto: %s', resp)
            
           

        return move