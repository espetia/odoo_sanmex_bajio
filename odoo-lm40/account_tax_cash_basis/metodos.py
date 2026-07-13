# -*- coding: utf-8 -*-

from odoo import models, api, _, fields
from odoo.exceptions import UserError, ValidationError
import odoo.addons.decimal_precision as dp
from odoo.tools import float_is_zero, float_compare
import json
import logging

_logger = logging.getLogger(__name__)

class AccountInvoice(models.Model):
    _inherit = "account.move"    
        
    
    def js_assign_outstanding_line(self, line_id):
        
        
        
        #invoice = self
        self.ensure_one ()
        credit_aml = self.env['account.move.line'].browse(line_id)
        #invoice = self.env['account.move'].search([('type','=','in_invoice'),('partner_id.anticipo_proveedor.id','=',credit_aml.account_id.id),('invoice_payment_state','=','not_paid'),('state','=','posted')])
        #_logger.error('inovice: %s', invoice)
        
        _logger.error('credit_aml: %s', credit_aml.account_id.id)
        aml_to_reconcile = False


            # Revisamos si se requiere poliza para reclasificar el Anticipo de Cliente
        if (self.type == 'in_invoice' and credit_aml.account_id.id == (self.partner_id.anticipo_proveedor and self.partner_id.anticipo_proveedor.id or False)):
            #credit_aml.account_id.id != invoice.partner_id.property_account_payable_id.id and \
            _loggerrrrrrrrrrr.error('tipofactura: %s', self.type)

            """if (invoice.type == 'out_invoice' and not invoice.partner_id.anticipo_cliente) or\
             (invoice.type == 'in_invoice' and not invoice.partner_id.anticipo_proveedor):
                raise UserError(_('The Partner has no Account defined for Supplier Advance Application. Please check.'))

            aml_obj = self.env['account.move.line']
            move_obj = self.env['account.move']
            #available_advance_amount_company_curr = credit_aml.amount_residual
            if credit_aml.currency_id: # Anticipo en ME
                if credit_aml.currency_id == invoice.currency_id: # Moneda Anticipo == Moneda Factura
                    available_advance_amount_invoice_curr = credit_aml.amount_residual_currency
                else: # Moneda Anticipo != Moneda Factura
                    available_advance_amount_invoice_curr = credit_aml.currency_id.with_context(date=credit_aml.date).compute(abs(credit_aml.amount_residual_currency), invoice.currency_id)
            elif invoice.currency_id == invoice.company_id.currency_id: # Moneda Anticipo MN == Moneda Factura MN
                available_advance_amount_invoice_curr = credit_aml.amount_residual
                _logger.error('available_advance_amount_invoice_curr: %s', available_advance_amount_invoice_curr)
            elif invoice.currency_id != invoice.company_id.currency_id: #  Moneda Anticipo MN, Moneda Factura ME
                available_advance_amount_invoice_curr = credit_aml.company_id.currency_id.with_context(date=credit_aml.date).compute(abs(credit_aml.amount_residual), invoice.currency_id)


            # Calculamos el porcentaje del Anticipo a aplicar a la factura
            factor = available_advance_amount_invoice_curr and (invoice.amount_residual / available_advance_amount_invoice_curr) or 0.0
            if abs(factor) > 1.0: 
                factor = 1.0 * (available_advance_amount_invoice_curr >= 0 and 1 or -1)

            advance_amount_mn = abs(factor * credit_aml.amount_residual)
            advance_currency = False
            if credit_aml.currency_id:
                advance_amount_me = abs(factor * credit_aml.amount_residual_currency)
                advance_currency = credit_aml.currency_id
            else:
                advance_amount_me = 0.0
                if invoice.currency_id != invoice.company_id.currency_id:
                    advance_amount_me = credit_aml.company_id.currency_id.with_context(date=credit_aml.date).compute(abs(credit_aml.amount_residual), invoice.currency_id)
                    advance_currency = invoice.currency_id


            journal_id = self.env['account.journal'].search([('anticipo','=',1),('type','=','purchase')], limit=1)
            if not journal_id:
                raise UserError(_('There is no Journal defined for Customer / Supplier Advance Application. Please check.'))

            move_dict = {
                'date'      : fields.Date.context_today(self),
                'ref'       : _('Pre-paid Application to Invoice: %s') % ((invoice.type=='out_invoice' and invoice.number or invoice.ref)),
                'narration' : _('Pre-paid Application to Invoice: %s') % ((invoice.type=='out_invoice' and invoice.number or invoice.ref)),
                'company_id': invoice.company_id.id,
                'journal_id': journal_id.id,
                }
            # Creamos la partida para la cuenta de Cliente / Proveedor
            aml_dict_partner = credit_aml.copy_data()[0]
            aml_dict_partner.update({
                'name'           : _('Pre-paid Application to Invoice: %s') % (invoice.ref or invoice.name),
                'account_id'     : invoice.partner_id.property_account_payable_id.id,
                'date_maturity'  : fields.Date.context_today(self),
                'debit'          : invoice.type=='in_invoice' and advance_amount_mn or 0,
                'credit'         : invoice.type=='out_invoice' and advance_amount_mn or 0,
                'currency_id'    : advance_currency and advance_currency.id or False,
                'amount_currency': (advance_amount_me and ((invoice.type=='in_invoice' and advance_amount_me) or (invoice.type=='out_invoice' and -advance_amount_me) or False)) or False,
                'partner_id'     : invoice.partner_id.id,
            })
            aml_dict_advance = aml_dict_partner.copy()
            aml_dict_advance.update({
                'account_id': (invoice.type=='in_invoice' and invoice.partner_id.anticipo_proveedor.id) or \
                              (invoice.type=='out_invoice' and invoice.partner_id.anticipo_cliente.id),
                'debit'     : aml_dict_partner['credit'],
                'credit'    : aml_dict_partner['debit'],
                'amount_currency': aml_dict_partner['amount_currency'] and -aml_dict_partner['amount_currency'] or 0.0,
            })
                ###################################################
                ###################################################
            fc_currency_id = credit_aml.currency_id and credit_aml.currency_id.id or credit_aml.company_id.currency_id.id
            lines = []
            _logger.error('available_advance_amount_invoice_curr1: %s', available_advance_amount_invoice_curr)
            _logger.error('amount_residual: %s', invoice.amount_total)
            factor_base = available_advance_amount_invoice_curr and (available_advance_amount_invoice_curr / invoice.amount_residual) or 0.0
            factor_base2 = available_advance_amount_invoice_curr and (available_advance_amount_invoice_curr / invoice.amount_total) or 0.0
            if abs(factor_base) > 1.0:
                factor_base = 1.0
                factor_base2 = invoice.amount_residual / invoice.amount_total
            for inv_line_tax in invoice.tax_line_ids.filtered(lambda r: r.tax_id.use_tax_cash_basis==True):
                src_account_id = inv_line_tax.tax_id.invoice_repartition_line_ids.account_id.id
                dest_account_id = inv_line_tax.tax_id.tax_cash_basis_account.id
                if not (src_account_id and dest_account_id):
                    raise UserError(_("Tax %s is not properly configured, please check." % (inv_line_tax.tax_id.name)))
                mi_company_curr_orig = 0.0
                mib_company_curr_orig = 0.0
                for move_line in invoice.line_ids:
                    if move_line.account_id.id == inv_line_tax.tax_id.invoice_repartition_line_ids.account_id.id:
                        mi_company_curr_orig = (move_line.debit + move_line.credit) * factor_base2 * (inv_line_tax.tax_id.amount >= 0 and 1.0 or -1.0)
                        mib_company_curr_orig = round(move_line.amount_base * factor_base2, 2)
                    
                    #################################
                if ((invoice.type=='out_invoice' and inv_line_tax.tax_id.amount >= 0.0) or \
                             (invoice.type=='in_invoice' and inv_line_tax.tax_id.amount < 0.0)):
                    debit = round(abs(mi_company_curr_orig),2)
                    credit = 0
                elif ((invoice.type=='in_invoice' and inv_line_tax.tax_id.amount >= 0.0) or \
                             (invoice.type=='out_invoice' and inv_line_tax.tax_id.amount < 0.0)):
                    debit = 0
                    credit = round(abs(mi_company_curr_orig),2)

                    #################################
                line2 = {
                        'name'            : inv_line_tax.tax_id.name + ((_(" - Fact: ") + (invoice.type=='out_invoice' and invoice.name or invoice.ref)) or 'N/A'),
                        'partner_id'      : invoice.partner_id.id, 
                        'debit'           : debit,
                        'credit'          : credit,
                        'account_id'      : src_account_id, 
                        'tax_id_secondary': inv_line_tax.tax_id.id,
                        'analytic_account_id': False,
                        'amount_base'     : abs(mib_company_curr_orig),
                    }

                line1 = line2.copy()
                line3 = {}
                xparam = self.env['ir.config_parameter'].get_param('tax_amount_according_to_currency_exchange_on_payment_date')[0]
                if not xparam == "1" or (invoice.company_id.currency_id.id == fc_currency_id == invoice.currency_id.id):
                    line1.update({
                        'name'        : inv_line_tax.tax_id.name + ((_(" - Fact: ") + (invoice.type=='out_invoice' and invoice.name or invoice.ref)) or 'N/A'),
                        'account_id'  : dest_account_id,
                        'debit'       : line2['credit'],
                        'credit'      : line2['debit'],
                        'amount_base' : line2['amount_base'],
                        })
                elif xparam == "1":
                    monto_base = round((inv_line_tax.tax_id.amount and advance_amount_mn \
                                                / (1.0 + (inv_line_tax.tax_id.amount / 100)) or (factor_base2 * inv_line_tax.amount_base_company_curr)), 2)
                    monto_a_reclasificar = round(inv_line_tax.tax_id.amount and monto_base * (inv_line_tax.tax_id.amount / 100) or 0.0,2)

                    line1.update({
                        'name': inv_line_tax.tax_id.name + ((_(" - Fact: ") + (invoice.type=='out_invoice' and invoice.number or invoice.reference)) or 'N/A'),
                        'debit': line2['credit'] and abs(monto_a_reclasificar) or 0.0,
                        'credit': line2['debit'] and abs(monto_a_reclasificar) or 0.0,
                        'account_id': dest_account_id,
                        'amount_base' : abs(monto_base),
                        })

                    if (round(mi_company_curr_orig, 2) - round(monto_a_reclasificar,2)):
                        amount_diff =  (round(abs(mi_company_curr_orig),2) - round(abs(monto_a_reclasificar),2)) * \
                                        (inv_line_tax.tax_id.amount >= 0 and 1.0 or -1.0)
                        line3 = {
                            'name': _('Diferencia de ') + inv_line_tax.tax_id.name + (invoice and (_(" - Fact: ") + (invoice.type=='out_invoice' and invoice.number or invoice.reference)) or 'N/A'),
                            'partner_id': invoice.partner_id.id,
                            'debit': ((amount_diff < 0 and invoice.type=='out_invoice') or (amount_diff >= 0 and invoice.type=='in_invoice')) and abs(amount_diff) or 0.0,
                            'credit': ((amount_diff < 0 and invoice.type=='in_invoice') or (amount_diff >= 0 and invoice.type=='out_invoice')) and abs(amount_diff) or 0.0,
                            'account_id': (amount_diff < 0 ) and invoice.company_id.income_currency_exchange_account_id.id or invoice.company_id.expense_currency_exchange_account_id.id,
                            'analytic_account_id': False,
                            }
                        
                lines += line3 and [(0,0,line1),(0,0,line2),(0,0,line3)] or [(0,0,line1),(0,0,line2)]
            lines += [(0,0, aml_dict_partner),(0,0, aml_dict_advance)] 
            _logger.error('lines: %s', lines)

            move_dict.update({'line_ids': lines})

            move = move_obj.create(move_dict)
            _logger.error('move: %s', move)
            move.post()
            aml_to_reconcile_advance = move.line_ids[0]
            # Creamos la partida para "descargar" la cuenta de Anticipo de Cliente / Proveedor
            aml_to_reconcile = move.line_ids[1]
            (aml_to_reconcile_advance + credit_aml).reconcile()
            _logger.error('aml_to_reconcile: %s', aml_to_reconcile)
            if aml_to_reconcile: # Se aplico Anticipo
                
                return self.action_register_payment(aml_to_reconcile)
            else:
                if not credit_aml.currency_id and invoice.currency_id != invoice.company_id.currency_id:
                    credit_aml.with_context(allow_amount_currency=True).write({
                        'amount_currency': invoice.company_id.currency_id.with_context(date=credit_aml.date).compute(credit_aml.balance, invoice.currency_id),
                        'currency_id': invoice.currency_id.id})
                

                    if credit_aml.payment_id:
                        credit_aml.payment_id.write({'invoice_ids': [(4, self.id, None)]})"""
    
        
        


class AccountPayment(models.Model):
    _inherit = "account.payment"


    @api.model
    def _create_move_line(self, move_id, line):
        sql = ""
        for l in line:
            l[2].update({'payment_id':self.id})
           
            sql_insert, sql_valores = "", ""
            for key, valor in l[2].items():
                sql_insert += "%s,\n" % (key)
                sep = not (type(valor) is float or type(valor) is int)
                sql_valores += "%s,\n" % (valor is not False and ((sep and "'%s'" or "%s") % (valor)) or 'null')

            sql += "insert into account_move_line (" + sql_insert + "create_uid, write_uid, create_date, write_date) values (" + sql_valores + \
                        ("%s,%s,%s,%s" % (self._uid, self._uid,"(now() at time zone 'UTC')", "(now() at time zone 'UTC')")) + ");"
        self._cr.execute(sql)
        return
    
    @api.model
    def _create_payment_entry(self, amount):
        _logger.error('amount: %s', amount)
        move = super(AccountPayment, self)._create_payment_entry(amount)
        tax_lines_dict = self._get_tax_paid_basis_entries(move)
        if tax_lines_dict:
            aml_obj = self.env['account.move.line']
            move.button_cancel()
            self.create_move_line(move.id, tax_lines_dict)
            move.post()
        return move


    
    def _get_tax_paid_basis_entries(self, move):
        """if not self.invoice_ids:
            return []"""
        #active_ids = [x.id for x in self.invoice_ids] 
        _loggerrrrrrrrrrr.error('active_ids: %s', active_ids)        
        currency_obj = self.env['res.currency']
        invoice_obj = self.env['account.move'] 
        _logger.error('invoice_obj: %s', invoice_obj)       
        move_id = move.id
        company_currency_id = self.company_id.currency_id
        payment_currency_id = self.currency_id or company_currency_id
        payment_amount_company_curr = 0  

        for pay in self.move_line_ids:
            payment_amount_company_curr += pay.debit          
            _logger.error('payment_amount_company_curr', payment_amount_company_curr)
        payment_amount_original_curr = self.amount
        invoice_currency_id = self.invoice_ids[0].currency_id
        currency_flag = False
           
        if company_currency_id.id == payment_currency_id.id == invoice_currency_id.id: # Invoice(s) & Payment in Company Currency
            payment_amount = payment_amount_company_curr
            currency_flag = True
            
        elif company_currency_id.id != payment_currency_id.id and payment_currency_id.id == invoice_currency_id.id: # Same Currency for Payment & Invoice(s) but not in company Currency
            payment_amount = payment_amount_original_curr                
        else: # Payment, Invoice(s) and Company Currency not equal from each other            
            payment_amount = payment_currency_id.with_context(date=self.payment_date).compute(payment_amount_original_curr, invoice_currency_id)
               
        invoice_ids = active_ids 
       
        invoices_grouped = {}
        self._cr.execute("""
                    select ai.id, (aml.debit + aml.credit) amount, aml.amount_currency, aml.currency_id
                    from account_move_line aml
                        inner join account_move am on am.id=aml.move_id
                        inner join account_account aa on aa.id=aml.account_id and aa.internal_type in ('payable', 'receivable')
                        inner join account_move ai on ai.move_id=am.id and ai.id in (""" + ','.join(str(e) for e in active_ids) + """) and ai.type in ('in_invoice', 'out_invoice')
                    --where not aml.reconciled
                    order by aml.date_maturity asc;
                """)
        
        cr_res = self._cr.fetchall()
        _logger.error('crres: %s', cr_res)
        sum_voucher_lines = 0.0
        i = 0
        for x in cr_res:
            #_logger.error('payment_amount_cr_res: %s', payment_amount)
            #_logger.error('equis: %s', x)
            val = {}
            val['invoice_id'], val['invoice_amount'], val['invoice_amount_currency'], val['invoice_currency_id'] = x[0], abs(x[1]), abs(x[2]), x[3],

            #if not payment_amount:
            #    continue           

            if payment_amount > (currency_flag and val['invoice_amount'] or val['invoice_amount_currency']):
                val['amount_assigned'] = (currency_flag and val['invoice_amount'] or val['invoice_amount_currency'])
                payment_amount = payment_amount - (currency_flag and val['invoice_amount'] or val['invoice_amount_currency'])
                _logger.error('invoice_amount_si: %s', val['amount_assigned'])
            elif payment_amount and payment_amount <= (currency_flag and val['invoice_amount'] or val['invoice_amount_currency']):
                debit = 0
                lines =[x.debit for x in self.move_line_ids.filtered(lambda r: r.debit>0)]                                                 
                
                #_logger.error('index: %s', i)                    
                debito = lines[i]                                                    
                _logger.error('DEbito: %s', debito)

                val['amount_assigned'] = debito                                
                #_logger.error('invoice_amount_elif: %s', val['amount_assigned'])
                i += 1   
                _logger.error('index_1: %s', x)
            #_logger.error('valores: %s', val)   
            key = (val['invoice_id'],val['invoice_currency_id'])            
            sum_voucher_lines += val['invoice_amount']
            
            if not key in invoices_grouped:
                invoices_grouped[key] = val
                _logger.error('invoices_grouped[key]_not: %s', invoices_grouped[key])
            else:
                invoices_grouped[key]['invoice_amount'] += val['invoice_amount']
                invoices_grouped[key]['invoice_amount_currency'] += val['invoice_amount_currency']
                invoices_grouped[key]['amount_assigned'] += val['amount_assigned']
                #_logger.error('invoices_grouped[key]_else: %s', invoices_grouped[key])
                
        precision = self.env['decimal.precision'].precision_get('Account')
        journal_id = self.journal_id.id
        date = self.payment_date
        currency_obj = self.env['res.currency']
        res = []

        for inv in invoices_grouped.values():
            factor_base = inv['invoice_amount'] / sum_voucher_lines
            #_logger.error('invamount: %s', inv['invoice_amount'])            
            #_logger.error('sum_voucher_lines1: %s', sum_voucher_lines)
            #_logger.error('factor_base: %s', factor_base)
            for invoice in invoice_obj.browse([inv['invoice_id']]):                
                factor = inv['amount_assigned'] / invoice.amount_total
                #_logger.error('amount_assigned_1: %s', inv['amount_assigned'])
                #_logger.error('invoice.amount_total: %s', invoice.amount_total) 
                #_logger.error('factor: %s', factor)               
                for inv_line_tax in invoice.tax_ids.filtered(lambda r: r.tax_id.use_tax_cash_basis==True):
                    src_account_id = inv_line_tax.tax_id.account_id.id
                    dest_account_id = inv_line_tax.tax_id.tax_cash_basis_account.id
                    if not (src_account_id and dest_account_id):
                        raise UserError(_("Tax %s is not properly configured, please check." % (inv_line_tax.tax_id.name)))
                    mib_company_curr_orig, mi_company_curr_orig = 0.0, 0.0
                    for move_line in invoice.move_id.line_ids:
                        if move_line.account_id.id == inv_line_tax.tax_id.account_id.id and \
                            move_line.tax_id_secondary.id == inv_line_tax.tax_id.id:
                            mi_company_curr_orig = (move_line.debit + move_line.credit) * factor
                            _logger.error('mi_company_curr_orig: %s', mi_company_curr_orig)
                            mib_company_curr_orig = move_line.amount_base * factor
                            _logger.error('mib_company_curr_orig: %s', mib_company_curr_orig)
                    if not mib_company_curr_orig and not inv_line_tax.tax_id.amount:
                        mib_company_curr_orig = inv_line_tax.amount_base_company_curr
                    #mi_invoice = inv_line_tax.amount * factor
                    #mib_invoice = mib_company_curr_orig / (mi_company_curr_orig / mi_invoice)                    
                    #################################
                    if ((invoice.type=='out_invoice' and inv_line_tax.tax_id.amount >= 0.0) or \
                                 (invoice.type=='in_invoice' and inv_line_tax.tax_id.amount < 0.0)):
                        debit = round(abs(mi_company_curr_orig),2) or 0.0
                        credit = 0.0
                        #amount_currency = (company_currency_id.id != invoice.currency_id.id) and abs(mi_invoice) or False
                    elif ((invoice.type=='in_invoice' and inv_line_tax.tax_id.amount >= 0.0) or \
                                 (invoice.type=='out_invoice' and inv_line_tax.tax_id.amount < 0.0)):
                        debit = 0.0
                        credit = round(mi_company_curr_orig,2) or 0.0
                        #amount_currency = (company_currency_id.id != invoice.currency_id.id) and -abs(mi_invoice) or False

                    #################################
                    line2 = {
                            'name'            : inv_line_tax.tax_id.name + ((_(" - Fact: ") + (invoice.type=='out_invoice' and invoice.number or invoice.reference)) or 'N/A'),
                            'quantity'        : 1,
                            'product_uom_id'  : False,
                            'partner_id'      : invoice.partner_id.id, 
                            'debit'           : debit,
                            'credit'          : credit,
                            'account_id'      : src_account_id, 
                            'journal_id'      : journal_id,
                            'period_id'       : move.period_id.id,
                            'company_id'      : invoice.company_id.id,
                            'move_id'         : move.id,
                            'tax_id_secondary': inv_line_tax.tax_id.id,
                            'analytic_account_id': False,
                            'date'            : date,
                            'date_maturity'   : date,
                            'amount_base'     : mib_company_curr_orig,
                        }

                    line1 = line2.copy()
                    line3 = {}
                    xparam = self.env['ir.config_parameter'].get_param('tax_amount_according_to_currency_exchange_on_payment_date')[0]
                    if not xparam == "1" or (company_currency_id.id == payment_currency_id.id == invoice.currency_id.id):
                        line1.update({
                            'name': inv_line_tax.tax_id.name + ((_(" - Fact: ") + (invoice.type=='out_invoice' and invoice.number or invoice.reference)) or 'N/A'),
                            'account_id'  : dest_account_id,
                            'debit'       : line2['credit'],
                            'credit'      : line2['debit'],
                            'amount_base' : line2['amount_base'],
                            #'amount_currency' : line2['amount_currency'] and -line2['amount_currency'] or False,
                            })
                    elif xparam == "1":
                        xfactor = float(inv_line_tax.amount_base / invoice.amount_total)
                        monto_base = round(factor_base * (\
                                            (inv_line_tax.tax_id.amount and (payment_amount_company_curr * xfactor)) \
                                                          or inv_line_tax.amount_base_company_curr), 2) 

                        monto_a_reclasificar = round(inv_line_tax.tax_id.amount and monto_base * (inv_line_tax.tax_id.amount / 100) or 0.0,2)
                        
                        
                        line1.update({
                            'name': inv_line_tax.tax_id.name + ((_(" - Fact: ") + (invoice.type=='out_invoice' and invoice.number or invoice.reference)) or 'N/A'),
                            'debit': line2['credit'] and abs(monto_a_reclasificar) or 0.0,
                            'credit': line2['debit'] and abs(monto_a_reclasificar) or 0.0,
                            'account_id': dest_account_id,
                            'amount_base' : abs(monto_base),
                            })

                        if (round(mi_company_curr_orig, 2) - round(monto_a_reclasificar,2)):
                            amount_diff =  (round(abs(mi_company_curr_orig),2) - round(abs(monto_a_reclasificar),2)) * \
                                            (inv_line_tax.tax_id.amount >= 0 and 1.0 or -1.0)
                            amount_diff = round(amount_diff,2)
                            line3 = {
                                'name': _('Diferencia de ') + inv_line_tax.tax_id.name + (invoice and (_(" - Fact: ") + (invoice.type=='out_invoice' and invoice.number or invoice.reference)) or 'N/A'),
                                'quantity': 1,
                                'partner_id': invoice.partner_id.id,
                                'debit': ((amount_diff < 0 and invoice.type=='out_invoice') or (amount_diff >= 0 and invoice.type=='in_invoice')) and abs(amount_diff) or 0.0,
                                'credit': ((amount_diff < 0 and invoice.type=='in_invoice') or (amount_diff >= 0 and invoice.type=='out_invoice')) and abs(amount_diff) or 0.0,
                                'account_id': (amount_diff < 0 ) and invoice.company_id.income_currency_exchange_account_id.id or invoice.company_id.expense_currency_exchange_account_id.id,
                                'journal_id': journal_id,
                                'period_id': move.period_id.id,
                                'company_id': invoice.company_id.id,
                                'move_id': move.id,
                                'analytic_account_id': False,
                                'date': date,
                                'date_maturity'   : date,
                                'currency_id': False,
                                'amount_currency' : False,
                                #'state' : 'valid',
                                }
                        else:
                            line3 = {}
                    lines = line3 and [(0,0,line1),(0,0,line2),(0,0,line3)] or [(0,0,line1),(0,0,line2)]
                    res += lines
                    #for resx in res:
                    #    print "resx: ", resx
                    #raise UserError('Pausa...')
        #return res