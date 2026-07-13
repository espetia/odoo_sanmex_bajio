# -*- coding: utf-8 -*-
###########################################################################

from odoo import models, fields, api, _
from odoo.exceptions import UserError



class AccountInvoice(models.Model):
    _inherit = "account.move"

    @api.model
    def register_payment(self, payment_line, writeoff_acc_id=False, writeoff_journal_id=False):
        """ Reconcile payable/receivable lines from the invoice with payment_line """
        line_to_reconcile = self.env['account.move.line']
        if payment_line.payment_id.invoice_ids or self._context.get('active_ids', False):
            self._cr.execute("""
                    select aml.id from account_move_line aml
                        inner join account_move am on am.id=aml.move_id
                        inner join account_account aa on aa.id=aml.account_id and aa.internal_type in ('payable', 'receivable')
                        inner join account_invoice ai on ai.move_id=am.id and ai.id in (""" + ','.join(str(e) for e in (self._ids or self._context.get('active_ids'))) + """)
                    where not aml.reconciled
                    order by aml.date_maturity asc;
                """)
            aml_ids = [x[0] for x in self._cr.fetchall()]
            return (line_to_reconcile.browse(aml_ids) + payment_line).reconcile(writeoff_acc_id, writeoff_journal_id)
        else:
            for inv in self:
                line_to_reconcile += inv.move_id.line_ids.filtered(lambda r: not r.reconciled and r.account_id.internal_type in ('payable', 'receivable'))
            return (line_to_reconcile + payment_line).reconcile(writeoff_acc_id, writeoff_journal_id)

