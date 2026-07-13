# -*- encoding: utf-8 -*-

from odoo import api, fields, models, _, tools
import logging
_logger = logging.getLogger(__name__)

class AccountInvoice(models.Model):
    _inherit = 'account.move'
    
    #@api.one
    @api.depends('line_ids.amount_residual')
    def _compute_payments(self):
        for record in self:           
            payment_lines = set()
            for line in record.line_ids.filtered(lambda l: l.account_id.id == record.partner_id.property_account_receivable_id.id):#self.account_id.id):
                
                payment_lines.update(line.mapped('matched_credit_ids.credit_move_id.id'))
                payment_lines.update(line.mapped('matched_debit_ids.debit_move_id.id'))
                _logger.info('Pagos: %s', payment_lines)
            record.payment_move_line_ids = self.env['account.move.line'].browse(list(payment_lines)).sorted()

    payment_line_ids = fields.One2many('account.payment.invoice', 'invoice_id', 'Pagos', readonly=True)
    payment_move_line_ids = fields.Many2many('account.move.line', string='Payment Move Lines', compute='_compute_payments', store=True)
