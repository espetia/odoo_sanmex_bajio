# -*- coding: utf-8 -*-

from odoo import api, fields, models, _, tools
from datetime import datetime
import time
from odoo import SUPERUSER_ID
import re
from odoo.exceptions import UserError, RedirectWarning, ValidationError
import logging
_logger = logging.getLogger(__name__)



class AccountInvoice(models.Model):
    _name = 'account.move'
    _inherit ='account.move'


    @api.depends('invoice_line_ids.price_subtotal', 'currency_id', 'company_id', 'invoice_date', 'move_type')
    def _compute_amount_total(self):
        for inv in self:
            amount_total_company_signed = inv.amount_total       
            if inv.currency_id and inv.company_id and inv.currency_id != inv.company_id.currency_id:
                currency_id = inv.currency_id.with_context(date=inv.invoice_date)
                amount_total_company_signed = currency_id.compute(inv.amount_total, inv.company_id.currency_id)
                
            sign = inv.move_type in ['in_refund', 'out_refund'] and -1 or 1
            inv.amount_total_company_signed = amount_total_company_signed * sign
            
    
    cancelacion_id = fields.Many2one('cancelaciones', string="Cancelación id")                
    UsoCFDI = fields.Many2one('sat.uso.cfdi', 'Uso CFDI', required=False, help='Define el motivo de la compra.') 
    status_cancel = fields.Char(string='Estatus de Cancelación', readonly=True)
    cancel_solicitud = fields.Many2one('cancelaciones', string="Solicitud de Cancelación", readonly=True, copy=False)
    MetodoPago = fields.Many2one('sat.metodo.pago','Metodo de Pago', help='Metodo de Pago Requerido por el SAT')
    type_rel_cfdi_ids = fields.One2many('sat.invoice.cfdi.rel', 'invoice_rel_id', 'CFDI Relacionados') 
    TipoCambio = fields.Float('Tipo Cambio', digits=(14,6), default=1.0)
    type_rel_id = fields.Many2one('sat.tipo.relacion.cfdi','Relacion CFDI')
    tipo_documento_id = fields.Many2one('tipo.documento', string='Tipo')
    tipo_documento_id_nc = fields.Many2one('tipo.documento', string='Tipo')
    deposit_invoice = fields.Boolean('Anticipo', compute='onchange_tipo_documento_id', store=True)
    amount_deposit = fields.Monetary('Monto de Anticipo')
    deposit_invoice_used = fields.Boolean('Anticipo Relacionado', help='Indica que esta factura ya fue relacionada en el XML de otra.', copy=False )
    tax_line_ids = fields.One2many('account.invoice.tax', 'invoice_id', string='Tax Lines', readonly=True, states={'draft': [('readonly', False)]}, copy=True)
    deposit_invoice_rel_id = fields.Many2one('account.move','Factura Relacionada como Anticipo', help='Indica a que factura fue relacionada en su XML.', copy=False )
    motivo_traslado_id = fields.Many2one('sat.traslado', 'Motivo de Traslado')
    tipo_operacion_id = fields.Many2one('sat.tipooperacion', 'Tipo de Operación')    

    forma_pago      = fields.Char(string="Forma de Pago", required=False, default="PAGO EN UNA SOLA EXHIBICION")
    
    invoice_datetime = fields.Datetime(string='Fecha Factura Electrónica ', readonly=True, 
                                       states={'draft': [('readonly', False)]}, copy=False,
                                      help="Keep empty to use the current date")
    date_invoice_tz = fields.Datetime(string='Date Invoiced with TZ', help='Date of Invoice with Time Zone', copy=False)
    Forma_Pago   = fields.Many2one('pay.method', string='Forma de Pago', readonly=True, 
                                      states={'draft': [('readonly', False)]})
    
    FormaPago  = fields.Many2many('pay.method', 'account_invoice_pay_method_rel', 'invoice_id', 'pay_method_id', 
                                       readonly=True, states={'draft': [('readonly', False)]},
                                       string="Formas de Pago")
    
    acc_payment     = fields.Many2one('res.partner.bank', string='Cuenta Bancaria', readonly=True, 
                                      states={'draft': [('readonly', False)]})
    

    direccion_compañia_id = fields.Many2one('res.partner', string='Dirección Emisión', store=True, compute='_get_address_issued_invoice')
    
    compañia_emisora_id = fields.Many2one('res.company',store=True, string='Compañía Emisora', compute='_get_address_issued_invoice')   
    timbre = fields.Char(readonly=True, copy=False)
    pac_timbre = fields.Char('Pac', readonly=True, copy=False)


    Sello             = fields.Text('Sello',  readonly=True, help='Sign assigned by the SAT', copy=False)
    NoCertificado    = fields.Char('No. Certificado Emisor', size=32, readonly=True,
                                       help='Serial Number of the Certificate', copy=False)
    cfdi_cadena_original   = fields.Text(string='Cadena Original', readonly=True,
                                        help='Original String used in the electronic invoice', copy=False)
    FechaTimbrado    = fields.Datetime(string='Fecha Timbrado', readonly=True,
                                           help='Date when is stamped the electronic invoice', copy=False)
    cfdi_fecha_cancelacion = fields.Datetime(string='Fecha Cancelación', readonly=True,
                                             help='Fecha cuando la factura es Cancelada', copy=False)
    UUID      = fields.Char(string='Folio Fiscal (UUID)', size=64, readonly=False,
                                     help='Folio Fiscal del Comprobante CFDI, también llamado UUID', copy=False)
    state_sat = fields.Selection([('validate', 'Timbrada'), ('no_cfdi', ' No Timbrada')], string="Estatus Sat", readonly=False, default='no_cfdi', copy=False)
    cfdi_cbb = fields.Binary('Imagen Código Bidimencional', copy=False)
    amount_to_text  = fields.Char(compute='_get_amount_to_text', string='Amount to Text', store=True,
                                help='Amount of the invoice in letter')
    sello = fields.Text('Sello', size=512, help='Digital Stamp', copy=False)
    certificado = fields.Text('Certificado', size=64, help='Certificate used in the invoice', copy=False)
    cadena_original = fields.Text('String Original', help='Data stream with the information contained in the electronic invoice')
    no_certificado  = fields.Char(string='No. Certificado Sat', size=64, help='Number of serie of certificate used for the invoice', copy=False)
    name_invoice = fields.Char(compute='_get_invoice', string='Factura')
    status_cfdi = fields.Char('Estatus CFDI', readonly=False, copy=False)
    cancel_appply = fields.Boolean('Cancelación aplicada')
    
    amount_total_company_signed = fields.Monetary(string='Total in Company Currency', currency_field='company_currency_id',
        store=True, readonly=True, compute='_compute_amount_total')

    periodicidad = fields.Many2one('sat.periodicidad', string='Periodicidad')
    meses_id = fields.Many2one('sat.meses', string='Meses')
    exportacion_id = fields.Many2one('sat.exportacion', string='Exportación')
    is_global = fields.Boolean('Factura global')
    year_report = fields.Char(string='Año Reportado')
    sale_dateil_ids = fields.One2many('sale.detail', 'invoice_id', string='Detalle de ventas', readonly=True)

    @api.onchange('partner_id')
    def _onchange_global_invoice(self):
        
        if self.partner_id.name == 'PUBLICO EN GENERAL':
            self.is_global = True
        else:

            self.is_global = False

    @api.onchange('invoice_payment_term_id')
    def onchange_metodo_pago_id(self):
        if self.invoice_payment_term_id:
            self.MetodoPago = self.invoice_payment_term_id.metodo_pago_id.id

    #@api.model
    @api.depends('journal_id')
    def _get_address_issued_invoice(self):
        self.direccion_compañia_id = self.journal_id.address_invoice_company_id or \
                                (self.journal_id.company2_id and self.journal_id.company2_id.address_invoice_parent_company_id) or False
        
        self.compañia_emisora_id = self.journal_id.company2_id #or self.journal_id or False

    @api.onchange('journal_id')
    def _onchange_journal_id_company(self):
        #res = super(AccountInvoice, self)._onchange_journal_id_company()
        self.direccion_compañia_id = self.journal_id.address_invoice_company_id
        self.compañia_emisora_id = self.journal_id.company2_id

    @api.onchange('currency_id','invoice_date')
    def onchange_currency_custom(self):
        diff_currency = self.currency_id != self.company_id.currency_id
        if diff_currency:
            _logger.info('funcion moneda')
            if self.currency_id or self.invoice_date:
                currency_second = self.currency_id.with_context(date=self.invoice_date or fields.Date.context_today(self))
                if currency_second:
                    self.TipoCambio = 1/(currency_second.rate or 1.0)
        else:
            self.TipoCambio = 1.0 
    #@api.model
    @api.onchange('tipo_documento_id')
    def onchange_tipo_documento_id(self): 
        journal_id = self.env['account.journal'].search([('anticipo','=',1),('type','=','sale')], limit=1)
        journal_id_customer = self.env['account.journal'].search([('anticipo','=',0),('type','=','sale')], limit=1)
        for res in self:       
            if res.tipo_documento_id:
                if res.tipo_documento_id.code == '002':
                    res.invoice_payment_term_id = res.tipo_documento_id.pay_term_id.id
                    res.MetodoPago = res.tipo_documento_id.forma_pago_id.id
                    res.UsoCFDI = res.tipo_documento_id.uso_cfdi_id.id 
                    res.deposit_invoice = True
                    #res.account_id = res.partner_id.anticipo_cliente.id or False
                    res.journal_id = journal_id.id
                    if not journal_id:
                        raise UserError(_('No esta definido el diaro para anticipos de clientes.'))
                   
                if res.tipo_documento_id_nc.code == '003':
                    res.account_id = res.partner_id.property_account_receivable_id
                    res.journal_id = journal_id_customer.id 
            
      
    @api.model_create_multi
    def create(self, vals_list):
        _logger.info('funcion venta') 
        res = super(AccountInvoice, self).create(vals_list)
        if res.tipo_documento_id:
            if res.tipo_documento_id.code == '002':
                res.invoice_payment_term_id = res.tipo_documento_id.pay_term_id.id
                res.MetodoPago = res.tipo_documento_id.forma_pago_id.id
                res.UsoCFDI = res.tipo_documento_id.uso_cfdi_id.id 
                res.deposit_invoice = True                 
                deposit_product_id = self.env['ir.config_parameter'].sudo().get_param('webservice.deposit_product_id')
                deposit_product_id = self.env['product.product'].browse(int(deposit_product_id)).exists()
                impuestos = [(4, tax.id, None) for tax in deposit_product_id.taxes_id]                
                tasa = deposit_product_id.taxes_id.amount
                subtotal_ant = (res.amount_deposit/(1 + (tasa/100.0)))
                _logger.error('subtotal: %s', subtotal_ant)
                if deposit_product_id.sat_product_id.franja_fronteriza and res.compañia_emisora_id.estimulo_sat and \
                 res.compañia_emisora_id.codigopostal_sat_id.franja_fronteriza:
                    impuestos = self.env['ir.config_parameter'].sudo().get_param('webservice.taxes_id')
                    impuestos = self.env['product.product'].browse(int(impuestos)).exists()                    
                    impuestos = [(4, impuestos, None)] 
                    
                if not deposit_product_id.property_account_income_id:
                    raise UserError(_("Error!\nProducto Anticipo sin configuración contable."))                         
                
                vals_list = {
                        'product_id': deposit_product_id.id, 
                        'name': deposit_product_id.name, 
                        'product_uom_id': deposit_product_id.uom_id.id, 
                        'quantity': 1, 
                        'objimp_id': 2,
                        'price_unit': subtotal_ant, 
                        'account_id': deposit_product_id.property_account_income_id.id, 
                        'move_id': res.id, 
                        'tax_ids': impuestos 
                        }
                _logger.error("Diccionario: %s", vals_list)
                l = self.env['account.move.line'].create(vals_list)  
                       
                _logger.error('l: %s', l)
                l.move_id.compute_taxes()
            res.invoice_line_ids.objimp_id = res.partner_id.objimp_id.id    
            
        return res         
   

    #@api.model
    def compute_taxes(self):
        
        account_invoice_tax = self.env['account.invoice.tax']
        ctx = dict(self._context)
        for invoice in self:
            # Delete non-manual tax lines
            self._cr.execute("DELETE FROM account_invoice_tax WHERE invoice_id=%s AND manual is False", (invoice.id,))
            if self._cr.rowcount:
                self.invalidate_cache()

            # Generate one tax line per tax, however many invoice lines it's applied to
            tax_grouped = invoice.get_taxes_values()
            #_logger.error('tax_grouped_consul: %s', tax_grouped)            
            for tax in tax_grouped.values():
                account_invoice_tax.create(tax)
        
        return self.with_context(ctx).write({'invoice_line_ids': []})

    @api.onchange('invoice_line_ids')
    def _onchange_invoice_line_ids_taxes(self):
        taxes_grouped = self.get_taxes_values()        
        tax_lines = self.tax_line_ids.filtered('manual')
        for tax in taxes_grouped.values():
            tax_lines += tax_lines.new(tax)            
        self.tax_line_ids = tax_lines
        

    def _prepare_tax_line_vals(self, line, tax): 
        #_logger.error('taxesvals: %s', tax)       
        vals = {
            'invoice_id': self.id,
            'name': tax['name'],
            'tax_id': int(re.findall('\d+', str(tax['id']))[0]),
            'amount': tax['amount'],
            'base': tax['base'],
            'manual': False,
            'sequence': tax['sequence'],
            'account_analytic_id': tax['analytic'] and line.account_analytic_id.id or False,
            'account_id': self.move_type in ('out_invoice', 'in_invoice', 'out_refund', 'in_refund') and (tax['account_id']),
        }
        
        
        if not vals.get('analytic_account_id') and line.analytic_account_id and vals['account_id'] == line.account_id.id:
            vals['analytic_account_id'] = line.analytic_account_id.id

        return vals

    
    def get_taxes_values(self):
        tax_grouped = {}        
        round_curr = self.currency_id.round
        for line in self.invoice_line_ids:
            price_unit = line.price_unit * (1 - (line.discount or 0.0) / 100.0)
            taxes = line.tax_ids.compute_all(price_unit, self.currency_id, line.quantity, line.product_id, self.partner_id)['taxes']
            #_logger.error("taescvalores: %s", taxes)
            for tax in taxes:
                val = self._prepare_tax_line_vals(line, tax)

                key = self.env['account.tax'].browse(tax['id']).get_grouping_key(val)
                #_logger.error('keygetvalues: %s', key)
                
                if key not in tax_grouped:
                    tax_grouped[key] = val
                    tax_grouped[key]['base'] = round_curr(val['base'])
                    tax_grouped[key]['tax_id'] = val['tax_id']
                    #_logger.error("tax_grouped[key]['tax_id']1: %s", tax_grouped[key]['tax_id'])
                else:
                    tax_grouped[key]['amount'] += val['amount']
                    tax_grouped[key]['base'] += round_curr(val['base'])
                    tax_grouped[key]['tax_id'] = val['tax_id']
                    #_logger.error("tax_grouped[key]['tax_id']: %s", tax_grouped[key]['tax_id'])
                
        return tax_grouped

    def _check_balanced(self):
        ''' Assert the move is fully balanced debit = credit.
        An error is raised if it's not the case.
        '''
        moves = self.filtered(lambda move: move.line_ids)
        if not moves:
            return

        # /!\ As this method is called in create / write, we can't make the assumption the computed stored fields
        # are already done. Then, this query MUST NOT depend of computed stored fields (e.g. balance).
        # It happens as the ORM makes the create with the 'no_recompute' statement.
        self.env['account.move.line'].flush(['debit', 'credit', 'move_id'])
        self.env['account.move'].flush(['journal_id'])
        self._cr.execute('''
            SELECT line.move_id, ROUND(SUM(line.debit - line.credit), currency.decimal_places)
            FROM account_move_line line
            JOIN account_move move ON move.id = line.move_id
            JOIN account_journal journal ON journal.id = move.journal_id
            JOIN res_company company ON company.id = journal.company_id
            JOIN res_currency currency ON currency.id = company.currency_id
            WHERE line.move_id IN %s
            GROUP BY line.move_id, currency.decimal_places
            HAVING ROUND(SUM(line.debit - line.credit), currency.decimal_places) != 0.0;
        ''', [tuple(self.ids)])

        query_res = self._cr.fetchall()
        if self.move_type not in ('out_invoice', 'out_refund', 'in_invoice', 'in_refund'):
            if query_res:
                ids = [res[0] for res in query_res]
                sums = [res[1] for res in query_res]
                raise UserError(_("Cannot create unbalanced journal entry. Ids: %s\nDifferences debit - credit: %s") % (ids, sums))

    
class AccountInvoiceLine(models.Model):
    _inherit = "account.move.line"  

    objimp_id = fields.Many2one('sat.objetoimp', string="ObjetoImp")
    no_ticket = fields.Char('Ticket')


    

    

    
class AccountMoveReversal(models.TransientModel):
    """
    Account move reversal wizard, it cancel an account move by reversing it.
    """
    _inherit = 'account.move.reversal'   
     
    def _prepare_default_reversal(self, move):
        reverse_date = self.date if self.date_mode == 'custom' else move.date
        return {
            'ref': _('Reversal of: %(move_name)s, %(reason)s', move_name=move.name, reason=self.reason) 
                   if self.reason
                   else _('Reversal of: %s', move.name),
            'date': reverse_date,
            'invoice_date': move.is_invoice(include_receipts=True) and (self.date or move.date) or False,
            'journal_id': self.journal_id.id,
            'invoice_payment_term_id': None,
            'tipo_documento_id': 1,
            'tipo_documento_id_nc': 3,
            'invoice_user_id': move.invoice_user_id.id,
            'auto_post': True if reverse_date > fields.Date.context_today(self) else False,
        }
class AccountPaymentTerm(models.Model):
    _name = 'account.payment.term'
    _inherit ='account.payment.term'

    metodo_pago_id = fields.Many2one('sat.metodo.pago','Metodo de Pago', help='Metodo de Pago Requerido por el SAT', )

class SatInvoiceCFDIRel(models.Model):
    _name = 'sat.invoice.cfdi.rel'
    _description = 'Relacion de CFDI'
    _rec_name = 'invoice_id' 

    invoice_id = fields.Many2one('account.move', 'Factura', required=True)
    invoice_rel_id = fields.Many2one('account.move', 'ID Rel')
    onchange_domain = fields.Boolean('Disparar Dominios', default=True)


    @api.onchange('onchange_domain')
    def onchange_relation(self):

        domain={}
        if self.invoice_rel_id.type_rel_id:
            if self.invoice_rel_id.type_rel_id.code == '07' and self.invoice_rel_id.type_rel_id.code == '04':
               domain.update(
                {
                    'invoice_id':[
                                  ('deposit_invoice','=',True),
                                  ('deposit_invoice_used','=',False),
                                  ('state','!=','draft'),
                                  ('move_type','in',('out_invoice','out_refund')),
                                  ('UUID','!=',False),
                                  ('partner_id','=',self.invoice_rel_id.partner_id.id)]
                }) 
            else:
                domain.update(
                    {
                        'invoice_id':[
                                      ('state','!=','draft'),
                                      ('move_type','in',('out_invoice','out_refund')),
                                      ('UUID','!=',False),
                                      ('partner_id','=',self.invoice_rel_id.partner_id.id)]
                    }) 

        else:
            domain.update(
                {
                    'invoice_id':[
                                  ('state','!=','draft'),
                                  ('move_type','in',('out_invoice','out_refund')),
                                  ('UUID','!=',False),
                                  ('partner_id','=',self.invoice_rel_id.partner_id.id)]
                })
        print('domain: ', domain)
        return {'domain': domain}

           
class TipoDocumento(models.Model):
  _name = "tipo.documento"

  code = fields.Char('Codigo')
  name = fields.Char('Descripción')
  forma_pago_id = fields.Many2one('sat.metodo.pago', 'Forma de Pago')
  uso_cfdi_id = fields.Many2one('sat.uso.cfdi', 'Uso CFDI')
  pay_term_id = fields.Many2one('account.payment.term', 'Plazo de pago')
  tipo = fields.Selection([('tipo_fac', 'Factura'), ('tipo_nc','Nota de crédito')], string="Tipo")
  

  #@api.multi
  @api.depends('name', 'code')
  def name_get(self):
      result = []
      for rec in self:
          if rec.name and rec.code:
              name = '[ '+rec.code+' ]' + ' ' + rec.name
              result.append((rec.id, name))
      return result

    
  @api.model
  def name_search(self, name, args=None, operator='ilike', limit=100):
      args = args or []
      domain = []
      if name:
          domain = ['|', ('code', '=ilike', name + '%'), ('name', operator, name)]
          if operator in expression.NEGATIVE_TERM_OPERATORS:
              domain = ['&', '!'] + domain[1:]
      recs = self.search(domain + args, limit=limit)
      return recs.name_get()

class AccountInvoiceTax(models.Model):
    _name = "account.invoice.tax"
    _description = "Invoice Tax"
    _order = 'sequence'

    @api.depends('invoice_id.invoice_line_ids')
    def _compute_base_amount(self):
        tax_grouped = {}
        for invoice in self.mapped('invoice_id'):
            tax_grouped[invoice.id] = invoice.get_taxes_values()            
            #_logger.error('taxesjjjjjjjjjj: %s', tax_grouped[invoice.id])
            
        for tax in self: 
            tax.base = 0.0
            #_logger.error('tax: %s', tax.tax_id)    
            if tax.tax_id:
            
                if tax.tax_id.tax_exigibility == 'on_payment':
                    account = tax.tax_id.cash_basis_transition_account_id
                else:
                        #account = repartition_line.account_id
                    account = tax.tax_id.cash_basis_base_account_id
                    _logger.error('cuenta: %s', account)
                key = tax.tax_id.get_grouping_key({
                    'tax_id': tax.tax_id.id,
                    'account_id': account.id,
                    'account_analytic_id': tax.account_analytic_id.id,

                })
                _logger.error('keyeerrtt: %s', key)
                if tax.invoice_id and key in tax_grouped[tax.invoice_id.id]:
                    tax.base = tax_grouped[tax.invoice_id.id][key]['base']  
                    tax.amount = tax_grouped[tax.invoice_id.id][key]['amount']          
                else:
                    _logger.warning('Tax Base Amount not computable probably due to a change in an underlying tax (%s).', tax.tax_id.name)

    invoice_id = fields.Many2one('account.move', string='Invoice', ondelete='cascade', index=True)
    name = fields.Char(string='Tax Description')
    tax_id = fields.Many2one('account.tax', string='Tax', ondelete='restrict')
    account_id = fields.Many2one('account.account', string='Tax Account', required=True, domain=[('deprecated', '=', False)])
    account_analytic_id = fields.Many2one('account.analytic.account', string='Analytic account')
    amount = fields.Monetary()
    amount_rounding = fields.Monetary()
    amount_total = fields.Monetary(string="Amount", compute='_compute_amount_total')
    manual = fields.Boolean(default=True)
    sequence = fields.Integer(help="Gives the sequence order when displaying a list of invoice tax.")
    company_id = fields.Many2one('res.company', string='Company', related='account_id.company_id', store=True, readonly=True)
    currency_id = fields.Many2one('res.currency', related='invoice_id.currency_id', store=True, readonly=True)
    base = fields.Monetary(string='Base', compute='_compute_base_amount', store=True)

   
    

    @api.depends('amount', 'amount_rounding')
    def _compute_amount_total(self):
        for tax_line in self:
            tax_line.amount_total = tax_line.amount + tax_line.amount_rounding

class AccountTax(models.Model):
    _inherit = 'account.tax'

    def get_grouping_key(self, invoice_tax_val):
        #key = super(AccountTax, self).get_grouping_key(invoice_tax_val)
        key = str(invoice_tax_val['tax_id']) + '-' + str(invoice_tax_val['account_id']) 
        return key
    




