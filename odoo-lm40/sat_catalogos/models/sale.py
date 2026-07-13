# -*- encoding: utf-8 -*-

from odoo import api, fields, models, _
from odoo.exceptions import UserError, RedirectWarning, ValidationError
import logging
_logger = logging.getLogger(__name__)


class SaleOrder(models.Model):
    _inherit = "sale.order"    
    
    
    acc_payment = fields.Many2one('res.partner.bank', string='Cuenta Bancaria', readonly=True, 
                                  states={'draft': [('readonly', False)], 'sent': [('readonly', False)]})
    
    pay_method_id = fields.Many2one('pay.method', string='Forma de Pago', readonly=True, 
                                  states={'draft': [('readonly', False)], 'sent': [('readonly', False)]})
    
    uso_cfdi_id = fields.Many2one('sat.uso.cfdi', 'Uso CFDI', readonly=True, 
                                  states={'draft': [('readonly', False)], 'sent': [('readonly', False)]}, 
                                  required=False, help='Define el motivo de la compra.', ) 
    partner_id = fields.Many2one(
        'res.partner', string='Cliente', readonly=True,
        states={'draft': [('readonly', False)], 'sent': [('readonly', False)]},
        required=True, change_default=True, index=True, tracking=1,
        domain="[('customer','=', True)]")

    
    def _prepare_invoice(self):  
        
        res = super(SaleOrder, self)._prepare_invoice()
        r = []
        resp = {}
        data = {}
        #for rec in self:
        #impuesto_line = self.env['account.tax'].search([('id','=',self.order_line.tax_id.id)])
        for line in self.order_line:

            #for imp in line.tax_id:
                
           
            #_logger.info('función dos')
            for tax in line.tax_id:
                impuesto_line = self.env['account.tax'].search([('id','=',tax.id)])
                price_reduce = line.price_unit * (1.0 - line.discount / 100.0)
                taxes = line.tax_id.compute_all(price_reduce, quantity=line.product_uom_qty, product=line.product_id)['taxes']
                group = tax.tax_group_id
                resp.setdefault(group, {'id': 0, 'amount': 0.0, 'base': 0.0})
           
                for t in taxes: 
                    #_logger.error('id: %s', t)  
                    if t['id'] == tax.id or t['id'] in tax.children_tax_ids.ids:
                        resp[group]['id'] = t['id']
                        resp[group]['amount'] += t['amount']
                        resp[group]['base'] += t['base']  
                    if tax['id']:
                       
                        data = {
                                'tax_id': tax['id'],
                                'name': tax['name'],
                                'account_id': impuesto_line.cash_basis_transition_account_id.id,
                                'manual': False,
                                'base': resp[group]['base'],
                                'amount': resp[group]['amount']
                                
                                }
                        _logger.error('impuestos: %s', data)
            
                existe = False
                posicion = -1
                if len(r) <= 0:
                    r.append(data)
                else:
                    for i in r:
                        posicion += 1
                        if i['tax_id'] == tax['id']:
                            existe = True
                            break

                    if existe == True:
                        r[posicion]['amount'] = data['amount']
                        r[posicion]['base'] = data['base']
                    else:
                        r.append(data)   
                #r.append(data)
        res.update({'FormaPago':self.pay_method_id and [(6,0, [self.pay_method_id.id])] or False,
                    'acc_payment': self.acc_payment and self.acc_payment.id or False,
                    'UsoCFDI': self.uso_cfdi_id and self.uso_cfdi_id.id or False, 
                    'tax_line_ids': r,   
                    'tipo_documento_id': 1,   

                    
        })
        
                  
        return res

    @api.model
    def default_get_sale(self, fields):
        rec = super(SaleOrder, self).default_get_sale(fields)              
        active_ids = self._context.get('active_ids')        
        if not active_ids:
            return rec
        invoices = self.env['account.move'].browse(active_ids)                
        invoice_ids = []
        if 'tax_line_ids' in fields:
            for invoice in invoices:
                invoice_ids.append(
                    [0, 0, {'tax_id': invoice.id,'invoice_currency_id': invoice.currency_id.id, 'total_factura': invoice.amount_total ,'saldo_pagar': invoice.amount_residual,'monto_pago': 0,} ]
                )        

        rec.update({
            'amount': 0.0,
            'payments_invoice_ids': invoice_ids
        })
        _logger.error('rec: %s', rec)
        return rec
    

"""class SaleAdvancePaymentInv(models.TransientModel):
    _inherit = "sale.advance.payment.inv"
    _description = "Sales Advance Payment Invoice"

    #@api.model
    def _get_advance_payment_method(self):
        if self._count() == 1:
            sale_obj = self.env['sale.order']
            order = sale_obj.browse(self._context.get('active_ids'))[0]
            if all([line.product_id.invoice_policy == 'order' for line in order.order_line]) or order.invoice_count:
                return 'all'
        return 'delivered'

    advance_payment_method = fields.Selection(selection_add=[('delivered', 'Invoiceable lines'), ('all', 'Invoiceable lines (deduct down payments)')], string='What do you want to invoice?', default=_get_advance_payment_method, required=True)"""

    
class SaleOrderLine(models.Model):
    _inherit = 'sale.order.line' 

    #@api.model
    def create(self, vals):
        
        res = super(SaleOrderLine, self).create(vals)
        impuestos = self.env['ir.config_parameter'].sudo().get_param('webservice.taxes_id')
        impuestos = self.env['product.product'].browse(int(impuestos)).exists()
        #impuesto = self.env['ir.config_parameter'].sudo().get_param('webservice.taxes_id')
        _logger.error("Impuestos: %s", impuestos)
        iva_8 = res.tax_id.filtered(lambda r: r.id == impuestos)
        _logger.error('Iva: %s', iva_8)
        if iva_8:

            if not res.product_id.sat_product_id.franja_fronteriza or not res.order_id.company_id.estimulo_sat or \
             not res.order_id.company_id.codigopostal_sat_id.franja_fronteriza:
                raise UserError('Error!\nNo aplica para Impuesto Tasa 8% .')
            
            
                
        return res  

    #@api.model
    def write(self, vals):
        
        res = super(SaleOrderLine, self).write(vals)
        #impuesto = self.env['ir.config_parameter'].sudo().get_param('webservice.taxes_id')
        impuestos = self.env['ir.config_parameter'].sudo().get_param('webservice.taxes_id')
        impuestos = self.env['product.product'].browse(int(impuestos)).exists()
        iva_8 = self.tax_id.filtered(lambda r: r.id == impuestos.id)
        if iva_8:

            if not self.product_id.sat_product_id.franja_fronteriza or not self.order_id.company_id.estimulo_sat or \
             not self.order_id.company_id.codigopostal_sat_id.franja_fronteriza:
                raise UserError('Error!\nNo aplica para Impuesto Tasa 8% .')
            
            
                
        return res

    def invoice_line_create(self, invoice_id, qty):
       
        invoice_lines = self.env['account.move.line']
        _logger.error('invoice_lines: %s', invoice_lines)
        precision = self.env['decimal.precision'].precision_get('Product Unit of Measure')
        for line in self:
            if not float_is_zero(qty, precision_digits=precision):
                vals = line._prepare_invoice_line(qty=qty)
                vals.update({'invoice_id': invoice_id, 'sale_line_ids': [(6, 0, [line.id])]})
                invoice_lines |= self.env['account.move.line'].create(vals)
        return invoice_lines
class reporAdvanceInvglobal(models.TransientModel):
    _name = "global.invoice.wizard"


    @api.model  
    def default_get(self, fields):
        res = super(reporAdvanceInvglobal, self).default_get(fields)
        record_ids = self._context.get('active_ids', [])
        sale_order_obj = self.env['sale.order']
        if not record_ids:
            return {}
        tickets = []  
        
        invoices = sale_order_obj.browse(record_ids)
        if any(inv.partner_id != invoices[0].partner_id for inv in invoices):
            raise UserError(_("Los Pedidos seleccionados no corresponden al mismo Cliente."))
        if any(inv.currency_id != invoices[0].currency_id for inv in invoices):
            raise UserError(_("Los Pedidos seleccionados no corresponden a la misma moneda."))
        
        
        for ticket in sale_order_obj.browse(record_ids):
           
            if ticket.invoice_status == 'invoiced':
                raise UserError(_("No se puede utilizar un pedido ya facturado"))
            
            
          
            if ticket:
            
                tickets.append((0,0,{
                        'ticket_id'     : ticket.id,
                        'date_order'    : ticket.date_order,
                        'sale_reference' : ticket.name,
                        'user_id'       : ticket.user_id.id,
                        'partner_id'    : ticket.partner_id and ticket.partner_id.id or False,
                        'amount_total'  : ticket.amount_total,
                        
                        }))
        res.update(ticket_ids=tickets)
        return res

    ticket_ids = fields.One2many('sale.order.global.invoice_wizard.line','wiz_id',string='Ventas a Facturar', required=True)
    periodicidad = fields.Many2one('sat.periodicidad', string='Periodicidad', required=True)
    meses_id = fields.Many2one('sat.meses', string='Meses', required=True)
    exportacion_id = fields.Many2one('sat.exportacion', string='Exportación', required=True)
    year_report = fields.Char(string='Año Reportado', required=True)
    pay_method_id = fields.Many2one('pay.method', string="Forma de Pago")

    def create_invoices(self):
        invoice_obj = self.env['account.move']
        invoice_ids = []        
        tickets_to_set_as_general_public = []
        lines_service = []
        tickets_simple_invoice =  []
        res = {}
        lines_to_invoice = []       
        
        ticket_id_list = []
        producto = self.env['product.product'].search([('name','=', 'Venta')])
        if not producto:
             raise UserError("No existe Concepto 'Venta' para la Factura global")
        else:
            for line in self.ticket_ids:
                tickets_to_set_as_general_public += line.ticket_id   
                taxes = producto.taxes_id.filtered(lambda r: not line.ticket_id.company_id or r.company_id == line.ticket_id.company_id)
                tax_ids = taxes.ids
                lines_service.append((0,0,{
                            
                             'name': producto.name,
                             'price_unit': line.ticket_id.amount_untaxed,
                             'quantity': 1.0,
                             'product_id': producto.id,
                             'product_uom_id': producto.uom_id.id,
                             'tax_ids': [(6, 0, tax_ids)],
                             'objimp_id': '3',
                             'no_ticket': line.ticket_id.name,
                            
                        }))
           
                line.ticket_id.invoice_status= 'invoiced'
                for concept in line.ticket_id.order_line:                    
                    #taxes_line = concept.product_id.taxes_id.filtered(lambda r: not line.ticket_id.company_id or r.company_id == line.ticket_id.company_id)
                    tax_ids_line = [(6, 0, concept.tax_id.ids)]
                    lines_to_invoice.append((0,0,{
                            
                            'concep_id': concept.product_id.id,
                            #'descripcion': concept.name,
                            'quantity': concept.product_uom_qty,                           
                            'discount': concept.discount,                         
                            'precio_unit':concept.price_unit,
                            'order_id': line.ticket_id.id,
                            'taxes_id': tax_ids_line,
                           
                            
                        }))
                
            cliente = self.env['res.partner'].search([('name','=', 'PUBLICO EN GENERAL')])
            metodo_pago = self.env['account.payment.term'].search([('metodo_pago_id.code','=', 'PUE')])
            tipo_factura = self.env['tipo.documento'].search([('code','=','005')])
            if not cliente:
                raise UserError("No existe cliente 'PUBLICO EN GENERAL'")
            else:
                invoice_vals = {
                            'ref': line.ticket_id.name,
                            'type': 'out_invoice',
                            'tipo_documento_id': tipo_factura.id,
                            'invoice_origin': line.ticket_id.name,
                            'invoice_user_id': line.ticket_id.user_id.id,                            
                            'partner_id': cliente.id,                    
                            'currency_id': line.ticket_id.pricelist_id.currency_id.id,
                            'UsoCFDI': cliente.uso_cfdi_id.id,
                            'periodicidad': self.periodicidad.id,
                            'meses_id': self.meses_id.id,
                            'exportacion_id': self.exportacion_id.id,
                            'is_global': True,
                            'FormaPago': self.pay_method_id and [(6,0, [self.pay_method_id.id])] or False,
                            'invoice_payment_term_id': metodo_pago.id,
                            'MetodoPago': metodo_pago.metodo_pago_id.id,
                            'year_report': self.year_report,
                            'invoice_line_ids': lines_service,    
                            'sale_dateil_ids': lines_to_invoice,             

                }
                _logger.error('valores: %s', invoice_vals)
                
                invoice_id = invoice_obj.create(invoice_vals)  
                invoice_id._recompute_tax_lines()                       
                invoice_id._onchange_invoice_line_ids_taxes()      
    


class sale_order_global_invoice_wizard_line(models.TransientModel):
    _name = "sale.order.global.invoice_wizard.line"
    

    wiz_id        = fields.Many2one('sale.order.invoice_wizard',string='ID Return', ondelete="cascade")
    ticket_id     = fields.Many2one('sale.order', string='Venta')
    date_order    = fields.Datetime(related='ticket_id.date_order', string="Fecha", readonly=True)
    sale_reference = fields.Char(related='ticket_id.name', string="Referencia", readonly=True)
    user_id       = fields.Many2one("res.users", related='ticket_id.user_id', string="Vendedor", readonly=True)
    amount_total  = fields.Float("Total", readonly=True)
    partner_id    = fields.Many2one("res.partner", related='ticket_id.partner_id', string="Cliente", readonly=True)

class DetalleInvoiceglobal(models.Model):
    _name = "sale.detail"


    @api.depends('precio_unit', 'quantity', 'discount')
    def _compute_amount_repor(self):
       
        for rec in self:
            #taxe_id = rec.concep_id.taxes_id
            #price = rec.precio_unit
            price = rec.precio_unit * (1 - (rec.discount or 0.0) / 100.0)
            taxes = self.taxes_id.compute_all(price, rec.order_id.currency_id, rec.quantity, product=rec.concep_id)
            rec.update({
                'price_tax': sum(t.get('amount', 0.0) for t in taxes.get('taxes', [])),
                'precio_total': taxes['total_included'],
                'precio_subtotal': taxes['total_excluded'],
            })

    invoice_id = fields.Many2one('account.move', string='Detalle de Ventas')
    order_id = fields.Many2one('sale.order', string="Orden de Venta")
    concep_id = fields.Many2one('product.product', string="Concepto")
    quantity = fields.Float('Cantidad')    
    precio_unit = fields.Float('Precio', digits='Product Price', default=0.0)
    precio_total = fields.Float(string='Importe', readonly=True, compute='_compute_amount_repor', store=True)    
    price_tax = fields.Float(string='Total impuestos', readonly=True, compute='_compute_amount_repor', store=True)
    precio_subtotal = fields.Float(string='Subtotal', readonly=True, compute='_compute_amount_repor', store=True)
    discount = fields.Float(string='Descuento (%)', digits='Discount', default=0.0)
    taxes_id = fields.Many2many('account.tax', string='Impuestos')