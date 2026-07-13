from odoo import api, models, fields, _
from odoo.exceptions import UserError
from odoo.tools import date_utils
import json
from odoo.tools import float_is_zero
from odoo.tools.float_utils import float_repr


class PurchaseOrder(models.Model):
    _inherit = 'purchase.order'

    payment_state = fields.Selection([
        ('no_bill', 'No Bill'), ('not_paid', 'Not Paid'),
        ('partial_paid', 'Partial Paid'), ('fully_paid', 'Fully Paid'),
        ('overdue', 'Overdue')], string='Payment Status', default='no_bill', copy=False, readonly=True,
        help="Payment Status.")

    compute_payment_state = fields.Char(string='Payment Status', compute='_show_payment_state', store=False,
                                        copy=False, default='no_bill', readonly=True,
                                        help="Payment Status.")

    ribbon_payment_state = fields.Char(string='Payment Status', store=False, default='no_bill',
                                       compute='_show_payment_state')

    show_payment_button = fields.Boolean(string='Show Payment Button', compute='_show_payment_button', store=False,
                                         copy=False)

    payments_widget = fields.Text(string='Payment Details',
                                  groups="account.group_account_invoice,account.group_account_readonly",
                                  compute='_compute_payments_widget_reconciled_info')

    order_amount_residual = fields.Monetary(string='Amount Due', compute='_compute_order_amount',
                                            help="Order Amount Due.")

    def _show_payment_state(self):
        for order in self:
            order.compute_payment_state = 'no_bill'
            if order.state in ['done', 'purchase']:
                order_amount_residual = float(float_repr(order.order_amount_residual,
                                                         precision_digits=order.currency_id.decimal_places))
                amount_total = order.amount_total
                if order_amount_residual == amount_total:
                    if order.invoice_ids:
                        order.compute_payment_state = 'not_paid'
                elif 0 < order_amount_residual < amount_total:
                    order.compute_payment_state = 'partial_paid'
                elif order_amount_residual == 0:
                    order.compute_payment_state = 'fully_paid'

            # Check payment overdue
            if order.compute_payment_state in ['partial_paid', 'not_paid']:
                today = fields.Date.context_today(self)
                if any(True for l in order.invoice_ids if l.invoice_date_due and l.invoice_date_due < today):
                    order.compute_payment_state = 'overdue'

            order.ribbon_payment_state = order.compute_payment_state

            if order.compute_payment_state != order.payment_state:
                order.payment_state = order.compute_payment_state

            if order.compute_payment_state == 'no_bill':
                order.compute_payment_state = 'No Bill'
            elif order.compute_payment_state == 'not_paid':
                order.compute_payment_state = 'Not Paid'
            elif order.compute_payment_state == 'partial_paid':
                order.compute_payment_state = 'Partial Paid'
            elif order.compute_payment_state == 'fully_paid':
                order.compute_payment_state = 'Fully Paid'
            elif order.compute_payment_state == 'overdue':
                diff = 0
                today = fields.Date.context_today(self)
                for l in order.invoice_ids:
                    if (today - l.invoice_date_due).days > diff:
                        diff = (today - l.invoice_date_due).days
                if diff == 1:
                    order.compute_payment_state = 'Overdue (yesterday)'
                elif diff > 1:
                    order.compute_payment_state = 'Overdue (%s days ago)' % str(diff)

    def _show_payment_button(self):
        self.show_payment_button = False
        invoice_not_paid = self.invoice_ids.filtered(lambda i: i.payment_state in ['not_paid', 'partial']
                                                               and i.move_type == 'in_invoice')
        if invoice_not_paid:
            self.show_payment_button = True

    def _compute_order_amount(self):
        for order in self:
            pl_order_amount_due = 0

            total_paid = 0
            if order.mapped("invoice_ids"):
                invoices = order.mapped("invoice_ids").filtered(
                    lambda i: i.state in ["posted"]
                              and i.move_type in ['in_invoice', 'in_receipt']
                              and i.payment_state not in ['paid']
                )
                if invoices:
                    for invoice in invoices:
                        total_paid += invoice.amount_total - invoice.amount_residual
                        pl_order_amount_due += invoice.amount_total

            billable_lines = order._get_billable_orderline()
            if billable_lines:
                pl_order_amount_due += sum(line.price_total for line in billable_lines)

            pl_order_amount_due = pl_order_amount_due - total_paid

            order.order_amount_residual = pl_order_amount_due if pl_order_amount_due > 0 else 0.0

    def _compute_payments_widget_reconciled_info(self):
        self.ensure_one()
        reconciled_vals = []
        payments_widget_vals = {'title': _('Less Payment'), 'outstanding': False, 'content': []}
        invoice_paid = self.invoice_ids.filtered(lambda i: i.payment_state in ['paid', 'partial']
                                                           and i.move_type == 'in_invoice')

        if invoice_paid:
            self._cr.execute('''
                        SELECT
                            payment.id,
                            payment.amount,
                            ARRAY_AGG(DISTINCT invoice.id) AS invoice_ids,
                            invoice.move_type
                        FROM account_payment payment
                        JOIN account_move move ON move.id = payment.move_id
                        JOIN account_move_line line ON line.move_id = move.id
                        JOIN account_partial_reconcile part ON
                            part.debit_move_id = line.id
                            OR
                            part.credit_move_id = line.id
                        JOIN account_move_line counterpart_line ON
                            part.debit_move_id = counterpart_line.id
                            OR
                            part.credit_move_id = counterpart_line.id
                        JOIN account_move invoice ON invoice.id = counterpart_line.move_id
                        JOIN account_account account ON account.id = line.account_id
                        WHERE account.internal_type IN ('payable')
                            AND invoice.id IN %(payment_ids)s
                            AND line.id != counterpart_line.id
                            AND invoice.move_type in ('in_invoice')
                        GROUP BY payment.id, invoice.move_type
                    ''', {
                'payment_ids': tuple(invoice_paid.ids)
            })

            query_res = self._cr.dictfetchall()

            if len(query_res):
                payment_id = []

                for res in query_res:
                    payment_id.append(res['id'])

                account_payment = self.env['account.payment'].search([('id', 'in', payment_id)])
                for p in account_payment:
                    reconciled_vals.append({
                        'name': p.name,
                        'journal_name': p.journal_id.name,
                        'amount': p.amount,
                        'currency': p.currency_id.symbol,
                        'digits': [69, p.currency_id.decimal_places],
                        'position': p.currency_id.position,
                        'date': p.date,
                        'account_payment_id': p.id,
                        'payment_method_name': p.payment_method_id.name if p.journal_id.type == 'bank' else None,
                        'ref': p.ref,
                        'no_unreconcile': 1,
                    })

                payments_widget_vals['content'] = reconciled_vals

        if payments_widget_vals['content']:
            self.payments_widget = json.dumps(payments_widget_vals, default=date_utils.json_default)
        else:
            self.payments_widget = json.dumps(False)

    def _get_billable_orderline(self, final=False):
        """Return the billable lines for order `self`."""

        billable_line_ids = []
        pending_section = None
        precision = self.env['decimal.precision'].precision_get('Product Unit of Measure')

        for line in self.order_line:
            if line.order_id.state not in ['purchase', 'done']:
                return []

            if line.display_type == 'line_section':
                # Only invoice the section if one of its lines is billable
                pending_section = line
                continue
            if line.display_type != 'line_note' and float_is_zero(line.product_uom_qty - line.qty_invoiced,
                                                                  precision_digits=precision):
                continue
            if line.product_uom_qty - line.qty_invoiced > 0 or (
                    line.product_uom_qty - line.qty_invoiced < 0 and final) or line.display_type == 'line_note':

                if pending_section:
                    billable_line_ids.append(pending_section.id)
                    pending_section = None
                billable_line_ids.append(line.id)

        return self.env['purchase.order.line'].browse(billable_line_ids)

    def action_register_payment(self):

        invoice_not_paid = self.invoice_ids.filtered(lambda i: i.payment_state in ['not_paid', 'partial']
                                                               and i.move_type == 'in_invoice')

        if not invoice_not_paid:
            raise UserError(_("You can't register a payment "
                              "because there is nothing left to pay on the selected journal items."))

        group_payment = len(invoice_not_paid) > 1

        return {
            'name': _('Register Payment'),
            'res_model': 'account.payment.register',
            'view_mode': 'form',
            'context': {
                'active_model': 'account.move.line',
                'active_ids': invoice_not_paid.line_ids.ids,
                'default_group_payment': group_payment,
            },
            'target': 'new',
            'type': 'ir.actions.act_window',
        }
