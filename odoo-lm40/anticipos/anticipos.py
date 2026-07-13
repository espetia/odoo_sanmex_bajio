from odoo import api, fields, models, _, tools

from odoo.exceptions import UserError, RedirectWarning, ValidationError
from odoo.osv import osv, expression
import logging
_logger = logging.getLogger(__name__)


class RegistrosAnticipos(models.Model):
    _name = 'anticipos'


    currency_id = fields.Many2one('res.currency', required=False, readonly=True,
        default=lambda self: self.env.user.company_id.currency_id.id)
    name = fields.Many2one('account.move', 'Factura', readonly=True)
    fecha_emision = fields.Date('Fecha de Emisión', readonly=True) 
    fecha_pago = fields.Date('Fecha de pago', readonly=True)
    type_document_id = fields.Many2one('tipo.documento', 'Tipo de Documento', readonly=True)
    monto_document = fields.Monetary('Monto', readonly=True)

    #@api.model
    @api.depends('monto_aplicado', 'total_pagos')
    def _aplicado(self):        
        self.monto_aplicado = self.total_pagos

    monto_aplicado = fields.Monetary('Monto Aplicado', compute="_aplicado", store=True, readonly=True)
    cliente_id = fields.Many2one('res.partner', 'Cliente', readonly=True)
    anticipos_ids = fields.One2many('anticipo.aplicado', 'anticipo_id', string="Anticipos Aplicados", readonly=True)

    #@api.model
    @api.depends('anticipos_ids.aplicado')
    def _total_anticipo(self):
        self.total_pagos = sum((line.aplicado if line.aplicado else 0.0) for line in self.anticipos_ids)

    total_pagos = fields.Monetary(string="Total Aplicado", compute='_total_anticipo', store=True)

    #@api.one
    @api.depends('monto_document', 'monto_aplicado', 'disponible')
    def _compute_monto(self):
        total = 0   
        total = self.monto_document - self.monto_aplicado
        _logger.error('Valor: %s', total)
        self.disponible = total

    disponible = fields.Monetary(string="Disponible", compute="_compute_monto", store=True) 
    
        


class AplicaAnticipo(models.Model):
    _name= 'anticipo.aplicado'


    anticipo_id = fields.Many2one('anticipos', string='Anticipo')
    folio_factura = fields.Many2one('account.move', 'Folio de Factura')
    folio_anticipo = fields.Many2one('account.move', string='Folio de Anticipo')
    folio_nc = fields.Many2one('account.move', 'Folio NC')    
    aplicado = fields.Monetary('Monto Aplicado')    
    fecha_Aplica = fields.Date('Fecha de Aplicación')    
    currency_id = fields.Many2one('res.currency', required=False, readonly=True,
        default=lambda self: self.env.user.company_id.currency_id.id)

class AccountInvoice(models.Model):
    _inherit = 'account.move'


    anticipo_id = fields.Many2one('anticipos', compute="_crear_anticipo", store=True)
    payment_ids = fields.Many2many('account.payment', 'account_invoice_payment_rel', 'invoice_id', 'payment_id', string="Payments", copy=False, readonly=True)
    #@api.model
    def action_cancel(self):

        res = super(AccountInvoice, self).action_cancel()
        anticipo = self.env['anticipo.aplicado'].search([('folio_nc','=',self.id)])        
        anticipo.unlink()
        return res

    
    @api.depends('payment_state', 'tipo_documento_id')
    def _crear_anticipo(self):
        for rec in self:
            if rec.payment_state in ('posted', 'in_payment') and rec.tipo_documento_id.code == '002' and rec.move_type in ('out_invoice'):
                rec.anticipo_id = rec.crear_anticipo()
            else:
                rec.anticipo_id = False
    
    
    
    def crear_anticipo(self):  
        val = self.prepara()
        _logger.error('Resultado1: %s', val)
        res = self.env['anticipos'].create(val)
        _logger.error('Resultado: %s', res)
        return res.id
        

    #@api.depends('payment_ids')
    def prepara(self):
        self.ensure_one()
        _logger.error('payments: %s', self.payment_ids)
        for rec in self:
            #pagos_asc = sorted(self.payment_ids, key=lambda r: r.payment_date)
            pagos_asc = fields.Datetime.now()
             # _logger.error('pagos: %s', pagos_asc)
            #fecha_pago = pagos_asc[-1].payment_date if pagos_asc else True
            val = {'cliente_id': rec.partner_id.id, 'fecha_pago': pagos_asc, 'currency_id': rec.env.user.company_id.currency_id.id, 'name': rec.id, 'fecha_emision': rec.invoice_date, 'type_document_id': rec.tipo_documento_id.id, 'monto_document': rec.amount_total}
        return val

    """@api.model
    def assign_outstanding_credit(self, credit_aml_id):
        res = super(AccountInvoice, self).assign_outstanding_credit(credit_aml_id) 
        
        credit_aml = self.env['account.move.line'].browse(credit_aml_id)
        _logger.error('Credito: %s', credit_aml)
        anticipo = credit_aml.invoice_id.origin        
        res_anticipo = self.env['account.move'].search([('move_name','=',anticipo),('tipo_documento_id.code','=','002')])
        _logger.error('Res_anticipo: %s', res_anticipo)
        anticipo_add = self.env['anticipos'].search([('name','=', res_anticipo.id)])
        anticipo_aplicado_obj = self.env['anticipo.aplicado']        
        _logger.error("Documento: %s", credit_aml.invoice_id.tipo_documento_id_nc.code)        
        rate = 1.0
        diff_currency = anticipo_add.currency_id != self.company_id.currency_id
        if diff_currency:
            rate = self.env['res.currency.rate'].search([('name','<=',anticipo_add.fecha_pago or fields.Date.context_today(self)),('currency_id','=', self.currency_id.id)], order='name desc', limit=1)
            rate = rate.rate_custom       
            
        _logger.error("Tipo de Cambio: %s", rate)
                
        if credit_aml.credit > (anticipo_add.disponible * rate) and credit_aml.invoice_id.tipo_documento_id_nc.code == '003' or credit_aml.payment_id:
            raise UserError('El monto a Abonar es mayor al saldo disponible; Saldo disponible: %s' %(anticipo_add.disponible) )
        else:
            if credit_aml.invoice_id.tipo_documento_id_nc.code == '003':  
                val = { 
                        'anticipo_id': anticipo_add.id,
                        'folio_factura': self.id,
                        'folio_nc': credit_aml.invoice_id.id,
                        'folio_anticipo': res_anticipo.id,
                        'fecha_Aplica': fields.Date.context_today(self),
                        'aplicado': credit_aml.credit/rate,
                        'currency_id': anticipo_add.currency_id.id
                }
                _logger.error("Anticipo: %s", val)
                anticipo_aplicado_obj.create(val)  
            if credit_aml.invoice_id.tipo_documento_id_nc.code == '004':
                val = { 
                        'anticipo_id': anticipo_add.id,
                        'folio_factura': self.id,
                        'folio_nc': credit_aml.invoice_id.id,
                        'folio_anticipo': res_anticipo.id,
                        'fecha_Aplica': fields.Date.context_today(self),
                        'aplicado': credit_aml.credit,
                        'currency_id': anticipo_add.currency_id.id
                }
                _logger.error("Anticipo: %s", val)
                anticipo_aplicado_obj.create(val)  

            
                
            return res"""

    
        


    
    

    
        