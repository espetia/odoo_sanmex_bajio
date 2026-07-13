# -*- coding: utf-8 -*-

from odoo import api, fields, models, _, tools


class AccountPayment(models.Model):
	_inherit = 'account.payment'


	uso_cfdi_id = fields.Many2one('sat.uso.cfdi', 'Uso de CFDI', default=lambda self: self.env['sat.uso.cfdi'].search([('code','=','P01')], limit=1))
	type_document_id = fields.Many2one('sat.tipo.comprobante', 'Tipo de comprobante', default=lambda self: self.env['sat.tipo.comprobante'].search([('code','=','P')], limit=1))
	pay_method_id = fields.Many2one('pay.method', 'Forma de Pago')

class AccountRegisterPayments(models.TransientModel):
	_inherit = 'account.payment.register'

	pay_method_id = fields.Many2one('pay.method', 'Forma de Pago')