# -*- encoding: utf-8 -*-

from odoo import api, fields, models, _, tools
from odoo.exceptions import UserError
from odoo.tools import DEFAULT_SERVER_DATETIME_FORMAT, DEFAULT_SERVER_DATE_FORMAT
import operator
from datetime import datetime
from . import amount_to_text_es_MX
import logging
import pytz
from odoo.tools.misc import formatLang, format_date, get_lang
import re
_logger = logging.getLogger(__name__)

MAP_INVOICE_TYPE_PAYMENT_SIGN = {
    'out_invoice': 1,
    'in_refund': 1,
    'in_invoice': -1,
    'out_refund': -1,
    'entry': -1,
}

class account_register_payments_invoice(models.TransientModel):
    _name = "account.register.payments.invoice"

    payment_custom_id = fields.Many2one('account.payment.register', string="Pago")
    invoice_id = fields.Many2one('account.move', string="Factura")
    invoice_currency_id = fields.Many2one('res.currency', string='Moneda de Factura')
    total_factura = fields.Float(string='Total Factura', digits=(12, 6), default=0.0)
    saldo_pagar = fields.Float(string='Saldo', digits=(12, 6), default=0.0)
    monto_pago = fields.Float(string='Monto a Aplicar', digits=(12, 6), default=0.0)
    monto_pago_currency = fields.Float(string='Monto a Aplicar M.N', digits=(12, 6), default=0.0)


class payment_register(models.TransientModel):
    _inherit = "account.payment.register"
    
    user_id = fields.Many2one('res.users', string='Usuario', readonly=True, default=lambda self: self.env.user)
    num_operacion = fields.Char('Número de Operación')    
    pay_method_id   = fields.Many2one('pay.method', string='Forma de Pago')  
    timbrar = fields.Boolean(string="Timbrar pago")
    payment_datetime_reception = fields.Datetime(string='Fecha Recepción de Pago')
    use_for_cfdi = fields.Boolean(related="journal_id.use_for_cfdi", readonly=True)    
    currency_rate = fields.Float(string='Tipo Cambio', digits=(12, 6), default=1.0)
    currency_id = fields.Many2one('res.currency', string='Currency', required=True, default=lambda self: self.env.user.company_id.currency_id)
    
    @api.onchange('journal_id', 'invoice_line_ids')
    def _onchange_journal(self):
        active_ids = self._context.get('active_ids')
        invoices = self.env['account.move'].browse(active_ids)
        if self.journal_id and invoices:
            if invoices[0].is_inbound():
                domain_payment = [('payment_type', '=', 'inbound'), ('id', 'in', self.journal_id.inbound_payment_method_line_ids.ids)]
            else:
                domain_payment = [('payment_type', '=', 'outbound'), ('id', 'in', self.journal_id.outbound_payment_method_line_ids.ids)]
            domain_journal = [('type', 'in', ('bank', 'cash')), ('company_id', '=', invoices[0].company_id.id)]
            return {'domain': {'payment_method_id': domain_payment, 'journal_id': domain_journal}}
        return {}

    @api.onchange('currency_id', 'date', 'journal_id')
    def onchange_currency_id_custom(self):
        diff_currency = self.currency_id != self.journal_id.company_id.currency_id
        if diff_currency:
            if self.currency_id or self.payment_date:
                currency_second = self.currency_id.with_context(date=self.payment_date or fields.Date.context_today(self))
                _logger.error('demooo: %s', currency_second)
                if currency_second:
                    self.currency_rate = (currency_second.rate_custom or 1.0)
        else:
            self.currency_rate = 1.0
    
    
    
    def _create_payment_vals_from_wizard(self):

        amount = self.amount

        
        res = super(payment_register, self)._create_payment_vals_from_wizard()
            
        res['currency_rate'] = self.currency_rate
        res['payment_datetime_reception'] = self.payment_datetime_reception
        res['pay_method_id'] = self.pay_method_id.id
        res['num_operacion'] = self.num_operacion
        res['timbrar'] = self.timbrar
        res['amount'] = abs(amount)
        res['currency_id'] = self.currency_id.id
        res['cmpl_type'] = self.cmpl_type
        res['other_payment'] = self.other_payment.id
        #_logger.error('res_multipagos: %s', res)
        return res

    @api.model
    def default_get(self, fields):
        rec = super(payment_register, self).default_get(fields)              
        active_ids = self._context.get('active_ids')        
        if not active_ids:
            return rec
        invoices = self.env['account.move'].browse(active_ids)
        invoice_ids = []
        if 'payments_invoice_ids' in fields:
            for invoice in invoices:
                invoice_ids.append(
                    [0, 0, {'invoice_id': invoice.id,'invoice_currency_id': invoice.currency_id.id, 'total_factura': invoice.amount_total ,'saldo_pagar': invoice.amount_residual,'monto_pago': 0,} ]
                )        

        rec.update({
            'amount': 0.0,
            'payments_invoice_ids': invoice_ids
        })
        #_logger.error('rec: %s', rec)
        return rec


    amount = fields.Monetary(string='Payment Amount', compute="_get_amount_pay", required=True)    
    payments_invoice_ids = fields.One2many('account.register.payments.invoice', 'payment_custom_id', string="Facturas")


    @api.depends('payments_invoice_ids')
    def _get_amount_pay(self):
        #if self.payments_invoice_ids.invoice_id.type in ('out_invoice', 'out_refund', 'in_invoice', 'in_refund')
        if self.payments_invoice_ids:
            if self.payments_invoice_ids.invoice_currency_id == self.currency_id:
                total_amount =  sum(inv.monto_pago * MAP_INVOICE_TYPE_PAYMENT_SIGN[inv.invoice_id.move_type] for inv in self.payments_invoice_ids)
                self.amount = abs(total_amount)
            #_logger.error('total_amount: %s', total_amount)

            else:
                total_amount =  sum(inv.monto_pago_currency * MAP_INVOICE_TYPE_PAYMENT_SIGN[inv.invoice_id.move_type] for inv in self.payments_invoice_ids)
                self.amount = abs(total_amount)
      

    
     
    @api.onchange('currency_id')
    def onchange_amount_currency(self):     
        for payment_invoice in self.payments_invoice_ids:
            if payment_invoice.invoice_currency_id != self.currency_id:  
                rate = payment_invoice.invoice_currency_id.with_context(date=self.payment_date).rate
                rate = 1 / (rate or 1)            
                payment_invoice.monto_pago =  payment_invoice.monto_pago_currency / rate
                #_logger.error('payment_invoice.monto_pago: %s', payment_invoice.monto_pago)    
    

    def _create_payments(self):
        self.ensure_one()
        batches = self._get_batches()
        edit_mode = self.can_edit_wizard and (len(batches[0]['lines']) == 1 or self.group_payment)

        to_reconcile = []
        #invoice = []
        if edit_mode:
            payment_vals = self._create_payment_vals_from_wizard()
            payment_vals_list = [payment_vals]
            to_reconcile.append(batches[0]['lines'])
        else:
            # Don't group payments: Create one batch per move.
            if not self.group_payment:
                new_batches = []
                for batch_result in batches:
                    for line in batch_result['lines']:
                        new_batches.append({
                            **batch_result,
                            'lines': line,
                        })
                batches = new_batches
            payment_vals_list = []
            for batch_result in batches:
                payment_vals_list.append(self._create_payment_vals_from_batch(batch_result))
                to_reconcile.append(batch_result['lines'])
        invoice = []

        currency = self.payments_invoice_ids.mapped('invoice_currency_id')
       
        for payment_invoice in self.payments_invoice_ids:
            if self.currency_id.id == currency.id:
                if payment_invoice.monto_pago > payment_invoice.invoice_id.amount_residual:
                    raise UserError('Algunos de los pagos aplicados es mayor al saldo de la factura! ')

                if payment_invoice.monto_pago <= 0:
                    raise UserError('Revise el Monto aplicado, no puede ser Negativo a igual a 0! ')
            #else:
                
               
            amount = self.amount#self.env['account.payment']._compute_payment_amount(payment_invoice, payment_invoice[0].invoice_currency_id, self.journal_id, self.payment_date)
            invoice.append({
                        'payment_type': ('inbound' if amount > 0 else 'outbound'),#self.payment_type,
                        'invoice_id': payment_invoice.invoice_id.id,
                        'invoice_currency_id': payment_invoice.invoice_id.currency_id.id,
                        'saldo_pagar': payment_invoice.invoice_id.amount_residual,
                        'monto_pago': payment_invoice.monto_pago,
                        'payment_date': self.payment_date,
                        'currency_rate': self.currency_rate,
                     })        
        payments = self.env['account.payment'].create(payment_vals_list)[0]

        #currency = self.payments_invoice_ids.mapped('invoice_currency_id')
       
        if edit_mode:
            for payment, lines in zip(payments, to_reconcile):
                # Batches are made using the same currency so making 'lines.currency_id' is ok.
                if payment.currency_id != lines.currency_id:
                    liquidity_lines, counterpart_lines, writeoff_lines = payment._seek_for_lines()
                    source_balance = abs(sum(lines.mapped('amount_residual')))
                    payment_rate = liquidity_lines[0].amount_currency / liquidity_lines[0].balance
                    source_balance_converted = abs(source_balance) * payment_rate

                    # Translate the balance into the payment currency is order to be able to compare them.
                    # In case in both have the same value (12.15 * 0.01 ~= 0.12 in our example), it means the user
                    # attempt to fully paid the source lines and then, we need to manually fix them to get a perfect
                    # match.
                    payment_balance = abs(sum(counterpart_lines.mapped('balance')))
                    payment_amount_currency = abs(sum(counterpart_lines.mapped('amount_currency')))
                    if not payment.currency_id.is_zero(source_balance_converted - payment_amount_currency):
                        continue

                    delta_balance = source_balance - payment_balance

                    # Balance are already the same.
                    if self.company_currency_id.is_zero(delta_balance):
                        continue

                    # Fix the balance but make sure to peek the liquidity and counterpart lines first.
                    debit_lines = (liquidity_lines + counterpart_lines).filtered('debit')
                    credit_lines = (liquidity_lines + counterpart_lines).filtered('credit')

                    payment.move_id.write({'line_ids': [
                        (1, debit_lines[0].id, {'debit': debit_lines[0].debit + delta_balance}),
                        (1, credit_lines[0].id, {'credit': credit_lines[0].credit + delta_balance}),
                    ]})
        
        payments.with_context(payment_invoice=invoice).action_post()
        

        domain = [('account_internal_type', 'in', ('receivable', 'payable')), ('reconciled', '=', False)]
        for payment, lines in zip(payments, to_reconcile):

            # When using the payment tokens, the payment could not be posted at this point (e.g. the transaction failed)
            # and then, we can't perform the reconciliation.
            if payment.state != 'posted':
                continue

            payment_lines = payment.line_ids.filtered_domain(domain)
            for account in payment_lines.account_id:
                (payment_lines + lines)\
                    .filtered_domain([('account_id', '=', account.id), ('reconciled', '=', False)])\
                    .reconcile()

        return payments
       

            


    def action_create_payments(self):
        
        payments = self._create_payments()
        #payment.with_context(payment_invoice=invoice).action_post()
        if self._context.get('dont_redirect_to_payments'):
            return True

        action = {
            'name': _('Payments'),
            'type': 'ir.actions.act_window',
            'res_model': 'account.payment',
            'context': {'create': False},
        }
        if len(payments) == 1:
            action.update({
                'view_mode': 'form',
                'res_id': payments.id,
            })
        else:
            action.update({
                'view_mode': 'tree,form',
                'domain': [('id', 'in', payments.ids)],
            })
        return action
        

        

        
 

    


class account_payment(models.Model):
    #_name ='account.payment'
    _inherit = 'account.payment'
    


    
    def _get_date_payment_tz(self):
        
        tz = self.env.user.partner_id.tz or 'America/Mexico_City' 
        
        local_date = datetime.now(pytz.timezone(tz))
        #_logger.error("Fecha actual: %s", local_date) 
        self.date_payment_tz = local_date      
        
    
    def _get_fname_payment(self):
        if not self.journal_id.use_for_cfdi or (self.payment_type != 'inbound' and self.partner_type != 'customer'):
            self.fname_payment = '.'
            return
        
        fname = (self.company_id.partner_id.rfc or self.company_id.partner_id.rfc) + '_' + \
                (self.name and self.name.replace('/','_').replace(' ','') or '')
        self.fname_payment = fname 
        
    
    @api.depends('amount','currency_id')
    def _get_amount_to_text(self):
        for rec in self:
            rec.amount_to_text = amount_to_text_es_MX.get_amount_to_text(rec, rec.amount, rec.currency_id.name)   

    
    @api.depends('journal_id')
    def _get_address_issued_payment(self):
        for rec in self:
            rec.address_issued_id = rec.journal_id.address_invoice_company_id or \
                                    (rec.journal_id.company2_id and rec.journal_id.company2_id.address_invoice_parent_company_id) or \
                                    rec.journal_id.company_id.address_invoice_parent_company_id or False
            rec.company_emitter_id = rec.journal_id.company2_id or rec.journal_id.company_id or False


    sat_uuid = fields.Char("UUID")
    sat_folio = fields.Char("CFDI Folio")
    sat_serie = fields.Char("CFDI Serie")   
    user_id = fields.Many2one('res.users', string='Usuario', readonly=True, default=lambda self: self.env.user)
    uso_cfdi_id = fields.Many2one('sat.uso.cfdi', 'Uso CFDI')#, default=lambda self: self.env['sat.uso.cfdi'].search([('code','=','P01')],limit=1)) 
    ticomprobante = fields.Many2one('sat.tipo.comprobante', string='Tipo de Comprobante')#, default=lambda self: self.env['sat.tipo.comprobante'].browse(['code','=','P'])) 
    fname_payment   =  fields.Char(compute='_get_fname_payment', string='Nombre Archivo de Pago')
    payment_datetime = fields.Datetime(string='Fecha Emisión CFDI', states={'draft': [('readonly', False)]}, copy=False)
    payment_datetime_reception = fields.Datetime(string='Fecha Recepción Pago', readonly=False, states={'draft': [('readonly', False)]}, copy=False)
    date_payment_tz = fields.Datetime(string='Fecha CFDI con TZ', compute='_get_date_payment_tz', copy=False)
    
    amount_to_text  = fields.Char(compute='_get_amount_to_text', string='Amount to Text', store=True)
    # Campos CFDI # 
    no_certificado  = fields.Char(string='No. Certificado Emisor', size=64, help='Number of serie of certificate used for the invoice')
    certificado     = fields.Text('Certificado', size=64, help='Certificate used in the invoice')
    sello           = fields.Text('Sello', size=512, help='Digital Stamp')
    cadena_original = fields.Text('Cadena Original', help='Data stream with the information contained in the electronic invoice') 
    
    cfdi_cbb = fields.Binary(string='Imagen Código Bidimensional', readonly=True, copy=False)
    cfdi_sello = fields.Text('Sello Sat',  readonly=True, help='Sign assigned by the SAT', copy=False)
    cfdi_no_certificado = fields.Char('No. Certificado SAT', size=32, readonly=True)
    cfdi_cadena_original = fields.Text(string='Cadena Original', readonly=True)
    fecha_timbrado = fields.Datetime(string='Fecha Timbrado', readonly=True)                                            
    UUID = fields.Char(string='Folio Fiscal (UUID)', size=64, readonly=True)    
    pac_timbre = fields.Char('Pac', readonly=True)
    status_cfdi = fields.Char('Estatus CFDI', readonly=True)
    ##################################
    address_issued_id = fields.Many2one('res.partner', compute='_get_address_issued_payment', 
                                        string='Dirección Emisión', store=True)    
    company_emitter_id = fields.Many2one('res.company', compute='_get_address_issued_payment', store=True,
                                         string='Compañía Emisora') 
    payment_invoice_line_ids = fields.One2many('account.payment.invoice', 'payment_id', 'Desglose Facturas Pagadas', readonly=True)
    num_operacion = fields.Char('Número de Operación')    
    pay_method_id   = fields.Many2one('pay.method', string='Forma de Pago', readonly=True, 
                                      states={'draft': [('readonly', False)], 'posted': [('readonly', False)]})    
    use_for_cfdi    = fields.Boolean(related="journal_id.use_for_cfdi", readonly=True)   
    timbrar = fields.Boolean(string="Timbrar pago")
    currency_rate = fields.Float(string='Tipo Cambio', digits=(12, 6), default=1.0)
    cfdi_fecha_cancelacion = fields.Datetime(string='Fecha Cancelación', readonly=True,
                                             help='Fecha cuando la factura es Cancelada', copy=False)
    cancel_solicitud = fields.Many2one('cancelaciones', string="Solicitud de Cancelación", readonly=True)

    invoice_ids = fields.Many2many('account.move', 'account_invoice_payment_rel', 'payment_id', 'invoice_id', string="Invoices", copy=False, readonly=True,
                                   help="""Technical field containing the invoice for which the payment has been generated.
                                   This does not especially correspond to the invoices reconciled with the payment,
                                   as it can have been generated first, and reconciled later""")
   
    
    """def name_get(self):
        return [(payment.id, payment.name or _('Draft Payment')) for payment in self]"""
        
    @api.depends('payment_invoice_line_ids')
    def _change_total(self):
        _logger.error('payment_invoice: %s', self.payment_invoice_line_ids)
        for x in self.payment_invoice_line_ids:
            self.total_invoice += x.monto_pago
            #_logger.error('total_invoice: %s', self.total_invoice)
    total_invoice = fields.Float(compute='_change_total', store= True, string='total facturas')        
    factor_global = fields.Float(related='payment_invoice_line_ids.factor_global', string='Factor', digits=(14,6), store= True)

    @api.onchange('currency_id', 'payment_date')
    def onchange_currency_id_custom(self):
        diff_currency = self.currency_id != self.company_id.currency_id
        if diff_currency:
            if self.currency_id or self.date:
                currency_second = self.currency_id.with_context(date=self.date or fields.Date.context_today(self))
                #logger.error('demooo: %s', currency_second)
                if currency_second:
                    self.currency_rate = (currency_second.rate_custom or 1.0)
        else:
            self.currency_rate = 1.0

        
    @api.model
    def _get_move_vals(self, journal=None):
        res = super(account_payment, self)._get_move_vals(journal)
        res['currency_rate'] =  self.currency_rate
        journal = journal or self.journal_id
        if not journal.sequence_id:
            raise UserError(_('Configuration Error !'), _('The journal %s does not have a sequence, please specify one.') % journal.name)
        if not journal.sequence_id.active:
            raise UserError(_('Configuration Error !'), _('The sequence of journal %s is deactivated.') % journal.name)
        name = self.move_name or journal.with_context(ir_sequence_date=self.date).sequence_id.next_by_id()
        return {
            'name': name,
            'date': self.date,
            'ref': self.communication or '',
            'company_id': self.company_id.id,
            'journal_id': journal.id,
            'currency_rate': self.currency_rate
        }
        logger.error('resres: %s', res)
        return res

       

    #@api.model
    def cancel(self):
        res = super(account_payment, self).action_cancel()
        invoices_pay = self.env['account.move'].search([('payment_line_ids.payment_id','=',self.id)])
        _logger.error('PAgos: %s', invoices_pay)
        if self.UUID and self.status_cfdi != 'Cancelado' and self.payment_type == 'inbound':
                raise UserError(_("No puedes cancelar un pago con timbre (UUID).\n\nPrimero debes enviar una solicitud de cancelación del CFDI y esperar respuesta."))

        for payment in invoices_pay:              
            payment.payment_line_ids.unlink() 

             
        for rec in self:
            for move in rec.payment_move_line_ids.mapped('move_id'):
                if rec.invoice_ids:
                    move.line_ids.remove_move_reconcile()
                #move.button_draft()       
                #move.button_cancel()
                #move.unlink()
            rec.state = 'cancel'     

        return res

               
    
class AccountPaymentInvoice(models.Model):
    _name = 'account.payment.invoice' 

    @api.depends('invoice_id', 'payment_id')
    def _get_currency_rate(self):
        for rec in self:

            if rec.payment_currency_id == rec.env.user.company_id.currency_id:
                rec.invoice_currency_rate = 1#abs(rec.invoice_id.amount_total_signed / rec.invoice_id.amount_total_company_signed)
                if rec.payment_id.total_invoice >= rec.invoice_id.amount_total_signed:
                    #_logger.error('payment_id: %s', rec.payment_id.total_invoice)
                    factor = 100 / rec.payment_id.total_invoice
                    rec.factor_global = factor
                    rec.factor_fact = (rec.monto_pago * factor) / 100            
                    rec.monto_pago_fac = rec.payment_amount * rec.factor_fact
                else:
                    #_logger.error('payment_id: %s', rec.payment_id.total_invoice)
                    factor = 100 / rec.payment_id.total_invoice
                    rec.factor_global = factor
                    rec.factor_fact = (rec.monto_pago * factor) / 100            
                    rec.monto_pago_fac = rec.payment_amount * rec.factor_fact
            else:
               

                rec.invoice_currency_rate = rec.payment_id.currency_rate#rec.invoice_id.currency_id.with_context(date=rec.payment_date or fields.Date.context_today(self))#abs(rec.invoice_id.amount_total_company_signed / rec.invoice_id.amount_total_signed)
                if rec.payment_id.total_invoice >= rec.invoice_id.amount_total_signed:
                    #_logger.error('payment_id: %s', rec.payment_id.total_invoice)
                    factor = 100 / rec.payment_id.total_invoice
                    rec.factor_global = factor
                    rec.factor_fact = (rec.monto_pago * factor) / 100            
                    rec.monto_pago_fac = rec.payment_amount * rec.factor_fact
                else:
                    #_logger.error('payment_id: %s', rec.payment_id.total_invoice)
                    factor = 100 / rec.payment_id.total_invoice
                    rec.factor_global = factor
                    rec.factor_fact = (rec.monto_pago * factor) / 100            
                    rec.monto_pago_fac = rec.payment_amount * rec.factor_fact
             
    
    payment_id  = fields.Many2one('account.payment', 'Pago', required=True)
    payment_state = fields.Selection([('draft', 'Draft'), ('posted', 'Posted'), ('sent', 'Sent'), ('reconciled', 'Reconciled'), ('cancelled', 'Cancelado')], string="Estado", readonly=True, related="payment_id.state")
    payment_currency_id = fields.Many2one('res.currency', string="Moneda de Pago", related='payment_id.currency_id', readonly=True)
    currency_id = fields.Many2one('res.currency', string="Moneda de Pago", related='payment_id.currency_id', readonly=True)
    payment_date = fields.Date(string="Fecha Pago", related='payment_id.date', readonly=True)
    payment_amount = fields.Monetary(string="Monto Pago", related='payment_id.amount', readonly=True)    
    invoice_id  = fields.Many2one('account.move', string='Factura', required=True)     
    invoice_folio = fields.Char(related='invoice_id.name', string='Folio', readonly=True)
    payment_method = fields.Many2one(related='invoice_id.MetodoPago', string='Método de pago', readonly=True)
    invoice_uuid = fields.Char(related='invoice_id.UUID', string='UUID', readonly=True)
    invoice_currency_id = fields.Many2one('res.currency', string="Moneda Factura", related='invoice_id.currency_id', readonly=True)
    invoice_currency_rate = fields.Float(compute='_get_currency_rate', string="Tipo de cambio", readonly=True)    
    parcialidad = fields.Integer('Parcialidad', default=1, required=True)
    saldo_anterior = fields.Float('Saldo Anterior', default=0.0, help="Saldo Anterior (en Moneda de la Factura)")
    monto_pago  = fields.Float('Monto Aplicado', default=0.0, help="Monto Pago (en Moneda de la Factura)")
    saldo_final = fields.Float('Saldo Insoluto', default=0.0, help="Saldo Insoluto (en Moneda de la Factura) después del pago")
    monto_pago_fac  = fields.Float(compute='_get_currency_rate', string='Monto Aplicado Fact', default=0.0, help="Monto Pago (en Moneda de la Factura)")
    factor_fact = fields.Float(compute='_get_currency_rate', string='Porcentaje de pago', digits=(14,6), readonly=True)
    factor_global = fields.Float(compute='_get_currency_rate', string='Porcentaje de factura', digits=(14,6), readonly=True)
    
