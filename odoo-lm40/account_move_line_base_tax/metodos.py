# -*- encoding: utf-8 -*-
from odoo import api, fields, models, _
from odoo.exceptions import UserError, RedirectWarning, ValidationError
import logging
_logger = logging.getLogger(__name__)

class AccountMoveLine(models.Model):
    _inherit = 'account.move.line'


    

    @api.onchange('account_id')
    def onchange_tax_secondary(self):
        tax_acc = False
        if self.account_id:
            _logger.error('account_idmov: %s', self.account_id)            
            tax_acc = self.env['account.tax'].search([('tax_cash_basis_account', '=', self.account_id.id)], limit=1)
            _logger.error('tax_acc: %s', tax_acc)
           
        self.tax_id_secondary = self.account_id and tax_acc and tax_acc.id or False
        

    """@api.model
    def write(self, vals):
        res = super(AccountMoveLine, self).write(vals)
        for line in self:
            if line.tax_id_secondary and line.tax_id_secondary.type_tax_use == 'purchase':
                cat_tax = line.tax_id_secondary.tax_category_id
                if cat_tax and cat_tax.name in ('IVA', 'IVA-EXENTO') and line.amount_base <= 0 and\
                        not line.not_move_diot:
                    raise UserError(_('Las líneas con impuesto de Compra necesitan un valor en el Monto Base...'))
                
        return res"""
    
    
    
class AccountInvoiceTax(models.Model):
    _inherit = "account.invoice.tax"

    
    #@api.model
    @api.depends('tax_id', 'amount')
    def _get_tax_base_amount(self):
        for line in self:
            line.amount_base = line.tax_id.amount and (line.amount / (line.tax_id.amount / 100.0)) or 0
            if not line.tax_id.amount and line.invoice_id.amount_untaxed:
                amount_base = 0.0
                for invoice_line in line.invoice_id.invoice_line_ids:
                    for tax in invoice_line.tax_ids:
                        if tax.id == line.tax_id.id:
                            amount_base += invoice_line.price_subtotal
                line.amount_base = amount_base
            line.amount_base_company_curr = line.amount_base
            if line.invoice_id.currency_id != line.invoice_id.company_id.currency_id:
                line.amount_base_company_curr = line.invoice_id.currency_id.with_context(date=line.invoice_id.invoice_date).compute(line.amount_base, line.invoice_id.company_id.currency_id)
            line.abs_amount = abs(line.amount)

class AccountInvoice(models.Model):
    _inherit = 'account.move'

    #@api.model
    def tax_line_move_line_get(self):
        res = []
        for tax_line in self.tax_line_ids:            
            res.append({
                'tax_line_id': tax_line.tax_id.id,
                'type': 'tax',
                'name': tax_line.name,
                'price_unit': tax_line.amount,
                'quantity': 1,
                'price': tax_line.amount,
                'account_id': tax_line.account_id.id,
                'account_analytic_id': tax_line.account_analytic_id.id,
                'invoice_id': self.id,
                'amount_base': tax_line.amount_base_company_curr or (not tax_line.tax_id.amount and tax_line.invoice_id.amount_untaxed or 0.0),
                            
                'tax_id_secondary': tax_line.tax_id.id or False,
                })
        _logger.error('detalles de impuestos: %s', res)    
        return res    
    
    
    #@api.model
    def line_get_convert(self, line, part):
        res = super(AccountInvoice, self).line_get_convert(line, part)
        res.update({
            'amount_base': line.get('amount_base', False),
            'tax_id_secondary': line.get('tax_id_secondary', False),
        })
        _logger.error('resimpuestos: %s', res)
        return res
                
