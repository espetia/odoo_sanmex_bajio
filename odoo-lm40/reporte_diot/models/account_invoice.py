# -*- encoding: utf-8 -*-

from odoo import api, fields, models, _
from odoo.exceptions import UserError
import odoo.addons.decimal_precision as dp
import time
import logging
_logger = logging.getLogger(__name__)

class AccountDIOT(models.Model):
    _name ='account.invoice.diot'

    ESTADOS = [
        ('draft', "Generada"),
        ('done', "Enviada")]

    num_pre_diot = fields.Char("Folio Interno", default=lambda self: _('New'), readonly=True)
    name = fields.Many2one('account.move', 'Número de Factura')
    declaracion_id = fields.Many2one('declaraciones.sat', 'Id de Declaración')
    num_pago = fields.Many2one('account.payment', 'Número de pago', readonly=True)
    rfc_prove = fields.Char('Rfc Proveedor', readonly=True)
    fecha_pago = fields.Date('Fecha de pago', readonly=True)
    monto_base = fields.Monetary('Monto Diot', readonly=True)
    tasa_pagada = fields.Char('Tasa del Impuesto', readonly=True)
    monto_impuesto = fields.Monetary('Monto del Impuesto')
    periodo_reportado = fields.Many2one('account.period', 'Periodo', readonly=True, default=lambda self: self.env['account.period'].search([('date_start', '<=', fields.Date.today()), ('date_stop', '>=', fields.Date.today()), ('company_id', '=', self.env.user.company_id.id),('special','=',False)], limit=1))
    
    @api.model
    @api.depends('account_lines_ids.account_id')
    def _compute_account(self):
        if self.account_lines_ids:
            vals = u', '.join([u'{0}'.format(line.account_name) for line in self.account_lines_ids ])
            #_logger.error("Valores: %s", vals)
            self.account_id = vals

    account_id = fields.Html(string='Cuentas de Gasto', compute='_compute_account')        
    user_id = fields.Many2one('res.users', string='Usuario', readonly=True)
    state = fields.Selection(ESTADOS, string="Estado", default='draft')
    currency_id = fields.Many2one('res.currency', string="Moneda", required=False, readonly=True,
        default=lambda self: self.env.user.company_id.currency_id.id)
    factor = fields.Float('Factor de Causación', readonly=True)
    monto_factura = fields.Monetary('Monto de Factura', readonly=True)
    total_iva = fields.Monetary("Total IVA", readonly=True)
    categoria_impuesto = fields.Char('Tipo Impuesto', readonly=True)
    proveedor = fields.Char('Proveedor', readonly=True)
    tasa_tax = fields.Char('Tasa')
    account_lines_ids = fields.One2many('account.lines', 'pre_diot_id', string="Lineas de Factura")
    account_tax = fields.Char('Cuenta de Impuestos')
    def copy_custom(self):
        default_data = self.default_get([])
        #_logger.error("default: %s", default_data)
        res = super(AccountDIOT, self).copy(default_data)
        return res
        
    @api.model
    def create(self, vals):        
        
        vals['num_pre_diot'] = self.env['ir.sequence'].next_by_code('pre_diot') or _('New')

        result = super(AccountDIOT, self).create(vals)
        return result

class AccountLines(models.Model):
    _name = "account.lines"

    pre_diot_id = fields.Many2one('account.invoice.diot', string="lineas")
    product_id = fields.Char('Concepto', readonly=True)
    amount_line = fields.Monetary('Monto', readonly=True)
    account_id = fields.Many2one('account.account', 'Cuenta de gasto', readonly=True)
    account_name = fields.Char('Cuenta de Gasto')
    currency_id = fields.Many2one('res.currency', required=False, readonly=True,
        default=lambda self: self.env.user.company_id.currency_id.id)    

class AccountPayment(models.Model):
    _inherit = "account.payment"
    

    #@api.model
    def cancel(self):

        res = super(AccountPayment, self).cancel()
        pre_diots = self.env['account.invoice.diot'].search([('num_pago','=',self.id)])
        
        for diot in pre_diots:
            if diot.state == 'done':
                
                diot_new = diot.copy_custom()
                diot_new.monto_impuesto = diot.monto_impuesto * -1
                diot_new.monto_base = diot.monto_base * -1
            else:
                diot.unlink()
        

        return res

    #@api.model
    def action_post(self):  
        vals = {}         
        vals_pre = {}
        vals_line = dict()
        res = super(AccountPayment, self).action_post()
        rate = 1.0
        diff_currency = self.currency_id != self.company_id.currency_id
        #_logger.error("effrer: %s", diff_currency)
        if diff_currency:
            rate = self.env['res.currency.rate'].search([('name','<=',self.date or fields.Date.context_today(self)),('currency_id','=', self.currency_id.id)], order='name desc', limit=1)
            rate = rate.rate_custom
            #_logger.error("Tipo de Cambio: %s", rate)
        if not 'payment_invoice' in self._context:    
            #_logger.info('función activada')        
            if 'active_id' in self._context:
                if self._context['active_model'] == 'account.move':
                    invoice = self.env['account.move'].browse(self._context['active_id'])            
                    for tax in invoice.tax_line_ids:                          
                        if tax.amount_total >= 0:                      
                            for payment in self: 
                                _logger.error('pagos: %s', len(self))
                                total_iva_1 = tax.base + tax.amount_total
                                factor = total_iva_1/invoice.amount_total                    
                                tasa_imp = tax.tax_id.amount/100                    
                                monto_base = (factor * self.amount) * rate
                                monto_base_1 = monto_base/(1 + tasa_imp)                    
                                impuesto_tasa = monto_base_1 * tasa_imp                                      
                                if self.payment_type == 'outbound' and self.partner_type == 'supplier':
                                    vals_pre['name'] = invoice.id  
                                    vals_pre['num_pago'] = self.id         
                                    vals_pre['rfc_prove'] = invoice.partner_id.rfc 
                                    vals_pre['proveedor'] = invoice.partner_id.name                                     
                                    vals_pre['fecha_pago'] = self.date               
                                    vals_pre['monto_base'] = monto_base_1
                                    vals_pre['monto_impuesto'] =  impuesto_tasa
                                    vals_pre['tasa_pagada'] = tax.name
                                    vals_pre['tasa_tax'] = tax.tax_id.amount
                                    vals_pre['user_id'] = self.env.user.id 
                                    vals_pre['factor'] = factor
                                    vals_pre['total_iva'] = total_iva_1
                                    vals_pre['monto_factura'] = invoice.amount_total
                                    vals_pre['categoria_impuesto'] = tax.tax_id.tax_category_id.name
                                    vals_pre['account_tax'] = str(tax.tax_id.tax_cash_basis_account.code) + tax.tax_id.tax_cash_basis_account.name
                                    #invoice.invoice_payment_state = 'paid'
                                    prediot_id = self.env['account.invoice.diot'].create(vals_pre)
                                    #res = super(AccountPayment, self).post()
                                    #_logger.error("prediot_id: %s", prediot_id)
                                    for line in invoice.invoice_line_ids:                                        
                                        for taxes in line.tax_ids:
                                            if taxes.amount == tax.tax_id.amount:                                            
                                                vals_line['pre_diot_id'] = prediot_id.id
                                                vals_line['product_id'] = line.name
                                                vals_line['account_id'] = line.account_id.id
                                                vals_line['account_name'] = str(line.account_id.code) + line.account_id.name
                                                vals_line['amount_line'] = line.price_subtotal
                                                
                                                self.env['account.lines'].create(vals_line)
                        else:
                            for payment in self:                        
                                total_iva = tax.amount_total * -1
                                factor = total_iva/(invoice.amount_total +  total_iva)                         
                                monto_base = (factor * (payment.amount + total_iva)) * rate                            
                                monto_facturas =  invoice.amount_total + total_iva                   
                                if payment.payment_type == 'outbound':
                                    vals['name'] = invoice.id  
                                    vals['num_pago'] = self.id         
                                    vals['rfc_prove'] = invoice.partner_id.rfc 
                                    vals['proveedor'] = invoice.partner_id.name                                      
                                    vals['fecha_pago'] = payment.date               
                                    vals['monto_base'] = monto_base
                                    vals['monto_impuesto'] =  monto_base
                                    vals['tasa_pagada'] = tax.name
                                    vals['tasa_tax'] = tax.tax_id.amount
                                    vals['user_id'] = self.env.user.id 
                                    vals['factor'] = factor
                                    vals['total_iva'] = total_iva
                                    vals['monto_factura'] = monto_facturas
                                    vals['categoria_impuesto'] = tax.tax_id.tax_category_id.name
                                    vals['account_tax'] = str(tax.tax_id.tax_cash_basis_account.code) + tax.tax_id.tax_cash_basis_account.name

                                    prediot_id = self.env['account.invoice.diot'].create(vals)
                                    for line in invoice.invoice_line_ids:                                        
                                        for taxes in line.tax_ids:
                                            if taxes.amount == tax.tax_id.amount:                                            
                                                vals_line['pre_diot_id'] = prediot_id.id
                                                vals_line['product_id'] = line.name
                                                vals_line['account_id'] = line.account_id.id
                                                vals_line['account_name'] = str(line.account_id.code) + line.account_id.name
                                                vals_line['amount_line'] = line.price_subtotal
                                                
                                                self.env['account.lines'].create(vals_line)

        #_logger.error('Contexto: %s', self._context)

        if 'payment_invoice' in self._context: 
            _logger.info('segunda función activada')
            for payment_inv in self._context['payment_invoice']:
                invoice = self.env['account.move'].browse(payment_inv['invoice_id'])               
                for tax in invoice.tax_line_ids:
                    
                        for payment in self: 
                            if tax.amount_total >= 0:
                                total_iva_1 = tax.base + tax.amount_total
                                factor = total_iva_1/invoice.amount_total                        
                                tasa_imp = tax.tax_id.amount/100                        
                                monto_base = (factor * payment_inv['monto_pago']) * rate
                                monto_base_1 = monto_base/(1 + tasa_imp)
                                impuesto_tasa = monto_base_1 * tasa_imp               
                                             
                                if payment.payment_type == 'outbound':
                                    vals['name'] = invoice.id 
                                    vals['num_pago'] = self.id        
                                    vals['rfc_prove'] = invoice.partner_id.rfc
                                    vals['proveedor'] = invoice.partner_id.name              
                                    vals['fecha_pago'] = self.date               
                                    vals['monto_base'] = monto_base_1
                                    vals['monto_impuesto'] =  impuesto_tasa
                                    vals['tasa_pagada'] = tax.name
                                    vals['tasa_tax'] = tax.tax_id.amount
                                    vals['user_id'] = self.env.user.id
                                    vals['factor'] = factor
                                    vals['total_iva'] = total_iva_1
                                    vals['monto_factura'] = invoice.amount_total
                                    vals['categoria_impuesto'] = tax.tax_id.tax_category_id.name
                                    vals['account_tax'] = str(tax.tax_id.tax_cash_basis_account.code) + tax.tax_id.tax_cash_basis_account.name
                                                            
                                    prediot_id = self.env['account.invoice.diot'].create(vals)
                                    for line in invoice.invoice_line_ids:                                        
                                        for taxes in line.tax_ids:
                                            if taxes.amount == tax.tax_id.amount:                                            
                                                vals_line['pre_diot_id'] = prediot_id.id
                                                vals_line['product_id'] = line.name
                                                vals_line['account_id'] = line.account_id.id
                                                vals_line['account_name'] = str(line.account_id.code) + line.account_id.name
                                                vals_line['amount_line'] = line.price_subtotal
                                                
                                                self.env['account.lines'].create(vals_line)
                            else:
                        
                                total_iva = tax.amount_total * -1
                                factor = total_iva/(invoice.amount_total + total_iva)                        
                                monto_base = (factor * (payment_inv['monto_pago'] + total_iva)) * rate                            
                                monto_facturas =  invoice.amount_total + total_iva                   
                                if payment.payment_type == 'outbound':
                                    vals['name'] = invoice.id  
                                    vals['num_pago'] = self.id         
                                    vals['rfc_prove'] = invoice.partner_id.rfc 
                                    vals['proveedor'] = invoice.partner_id.name                                      
                                    vals['fecha_pago'] = self.date               
                                    vals['monto_base'] = monto_base
                                    vals['monto_impuesto'] =  monto_base
                                    vals['tasa_pagada'] = tax.name
                                    vals['tasa_tax'] = tax.tax_id.amount
                                    vals['user_id'] = self.env.user.id 
                                    vals['factor'] = factor
                                    vals['total_iva'] = total_iva
                                    vals['monto_factura'] = monto_facturas
                                    vals['categoria_impuesto'] = tax.tax_id.tax_category_id.name
                                    vals['account_tax'] = str(tax.tax_id.tax_cash_basis_account.code) + tax.tax_id.tax_cash_basis_account.name
                                    prediot_id = self.env['account.invoice.diot'].create(vals)

                                    for line in invoice.invoice_line_ids:                                        
                                        for taxes in line.tax_ids:
                                            if taxes.amount == tax.tax_id.amount:                                            
                                                vals_line['pre_diot_id'] = prediot_id.id
                                                vals_line['product_id'] = line.name
                                                vals_line['account_id'] = line.account_id.id
                                                vals_line['account_name'] = str(line.account_id.code) + line.account_id.name
                                                vals_line['amount_line'] = line.price_subtotal
                                                
                                                self.env['account.lines'].create(vals_line)

        return res

class AccountInvoice(models.Model):
    _inherit = "account.move" 

    is_regen = fields.Boolean('Factura nueva', default=False)

    def copy_custom(self):
        default_data = self.default_get([])
        _logger.error("default: %s", default_data)
        self.is_regen = True
        res = super(AccountInvoice, self).copy(default_data)

        return res   
        
    @api.model
    def _get_reconciled_info_JSON_values(self):
        vals = {}
        vals_line = dict()
        res = super(AccountInvoice, self)._get_reconciled_info_JSON_values()
        #
        pay_term_line_ids = self.line_ids.filtered(lambda line: line.account_id.user_type_id.type in ('receivable', 'payable'))
        
        partials = pay_term_line_ids.mapped('matched_debit_ids') + pay_term_line_ids.mapped('matched_credit_ids')
        
        for partial in partials:
            counterpart_lines = partial.debit_move_id + partial.credit_move_id
            
            counterpart_line = counterpart_lines.filtered(lambda line: line not in self.line_ids)
            
            
            invoice = self
                  
            for tax in self.tax_line_ids:        
                if tax.amount_total >= 0: 
                    total_iva_1 = tax.base + tax.amount_total
                    factor = total_iva_1/self.amount_total                        
                    tasa_imp = tax.tax_id.amount/100                        
                    monto_base = (factor * counterpart_line.debit)
                    monto_base_1 = monto_base/(1 + tasa_imp)
                    impuesto_tasa = monto_base_1 * tasa_imp                     
                    if counterpart_line.payment_id.payment_type == 'outbound':
                        vals['name'] = self.id 
                        vals['num_pago'] = counterpart_line.payment_id.id       
                        vals['rfc_prove'] = self.partner_id.rfc  
                        vals['proveedor'] = self.partner_id.name             
                        vals['fecha_pago'] = counterpart_line.date               
                        vals['monto_base'] = monto_base_1
                        vals['monto_impuesto'] =  impuesto_tasa
                        vals['tasa_pagada'] = tax.name
                        vals['tasa_tax'] = tax.tax_id.amount
                        vals['user_id'] = self.env.user.id
                        vals['factor'] = factor
                        vals['total_iva'] = total_iva_1
                        vals['monto_factura'] = self.amount_total
                        vals['categoria_impuesto'] = tax.tax_id.tax_category_id.name
                        vals['account_tax'] = str(tax.tax_id.tax_cash_basis_account.code) + tax.tax_id.tax_cash_basis_account.name
                        """prediot_id = self.env['account.invoice.diot'].create(vals)
                        _logger.info('función añadir pago')
                        for line in invoice.invoice_line_ids:                                        
                            for taxes in line.tax_ids:
                                if taxes.amount == tax.tax_id.amount:                                            
                                    vals_line['pre_diot_id'] = prediot_id.id
                                    vals_line['product_id'] = line.name
                                    vals_line['account_id'] = line.account_id.id
                                    vals_line['account_name'] = str(line.account_id.code) + line.account_id.name
                                    vals_line['amount_line'] = line.price_subtotal                                
                                    self.env['account.lines'].create(vals_line)"""
                else:
                    total_iva = tax.amount_total * -1
                    factor = total_iva/(invoice.amount_total +  total_iva)               
                    monto_base = factor * (counterpart_line.debit + total_iva)                            
                    monto_facturas =  invoice.amount_total + total_iva                   
                    if counterpart_line.payment_id.payment_type == 'outbound':
                        vals['name'] = self.id  
                        vals['num_pago'] = counterpart_line.payment_id.id         
                        vals['rfc_prove'] = self.partner_id.rfc  
                        vals['proveedor'] = self.partner_id.name                                     
                        vals['fecha_pago'] = counterpart_line.date               
                        vals['monto_base'] = monto_base
                        vals['monto_impuesto'] =  monto_base
                        vals['tasa_pagada'] = tax.name
                        vals['tasa_tax'] = tax.tax_id.amount
                        vals['user_id'] = self.env.user.id 
                        vals['factor'] = factor
                        vals['total_iva'] = total_iva
                        vals['monto_factura'] = monto_facturas
                        vals['categoria_impuesto'] = tax.tax_id.tax_category_id.name
                        vals['account_tax'] = str(tax.tax_id.tax_cash_basis_account.code) + tax.tax_id.tax_cash_basis_account.name
                        #prediot_id = self.env['account.invoice.diot'].create(vals)
                        """for line in invoice.invoice_line_ids:                                        
                            for taxes in line.tax_ids:
                                if taxes.amount == tax.tax_id.amount:                                            
                                    vals_line['pre_diot_id'] = prediot_id.id
                                    vals_line['product_id'] = line.name
                                    vals_line['account_id'] = line.account_id.id
                                    vals_line['account_name'] = str(line.account_id.code) + line.account_id.name
                                    vals_line['amount_line'] = line.price_subtotal                                
                                    self.env['account.lines'].create(vals_line)"""
        return res
