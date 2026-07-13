# -*- encoding: utf-8 -*-
from odoo import api, fields, models, _
from odoo.exceptions import UserError, RedirectWarning, ValidationError


class AccountMoveLine(models.Model):
    _inherit = 'account.move.line'

    amount_base      = fields.Float(string='Monto Base', help='Monto base sin impuestos...', store=True)
    tax_id_secondary = fields.Many2one('account.tax', string='Impuesto', help='Tax used for this move')
    not_move_diot    = fields.Boolean('No es para Diot',
                                      help='Si se activa este campo, aunque la partida tenga información relacionada a Proveedores (DIOT) no se tomará en cuenta para el reporte de la DIOT...')
class AccountMove(models.Model):
    _inherit = "account.move"

    item_concept = fields.Char(string='Concepto', size=300)
    
class AccountInvoiceTax(models.Model):
    _inherit = "account.invoice.tax"

        
    company_currency_id = fields.Many2one('res.currency', related='invoice_id.company_currency_id', readonly=True)
    amount_base = fields.Monetary(compute='_get_tax_base_amount', string='Monto Base', 
                               help='Monto Base en Moneda de Factura', store=True)
    amount_base_company_curr = fields.Monetary(compute='_get_tax_base_amount', string='Tax Base Amount in Company Currency', 
                                               currency_field='company_currency_id', store=True,
                                            help='Tax amount base in Company Currency')
    abs_amount  =   fields.Monetary(compute='_get_tax_base_amount', string='abs(Monto)', store=True,
                                               currency_field='company_currency_id')
    