# -*- coding: utf-8 -*-

from odoo import models, fields, api

class PurchaseOrder(models.Model):
    _inherit = 'purchase.order'

    exceptional_purchase_order = fields.Boolean(string='Exceptional Purchase Order', default=False)
    internal_note = fields.Text(string='Internal Note')
    payment_date = fields.Date(string='Payment Date')
    payment_documentation_line_ids = fields.One2many(
        'purchase.payment.documentation.line', 
        'order_id', 
        string='Payment Documentation Lines'
    )
    is_amount_exceeded = fields.Boolean(
        string='Is Amount Exceeded', 
        compute='_compute_payment_documentation_alerts'
    )
    is_ppd_missing = fields.Boolean(
        string='Is PPD Missing', 
        compute='_compute_payment_documentation_alerts'
    )

    @api.depends('payment_documentation_line_ids.amount', 'payment_documentation_line_ids.payment_method', 'amount_total', 'methodo_pago')
    def _compute_payment_documentation_alerts(self):
        for order in self:
            total_doc_amount = sum(order.payment_documentation_line_ids.mapped('amount'))
            order.is_amount_exceeded = (total_doc_amount - order.amount_total) > 1

            has_ppd_line = any(line.payment_method == 'PPD' for line in order.payment_documentation_line_ids)
            order.is_ppd_missing = getattr(order, 'methodo_pago', False) == 'PPD' and not has_ppd_line

    @api.model
    def _cron_send_ppd_missing_reminder(self, start_date=None):
        from datetime import date, timedelta
        
        today = fields.Date.context_today(self)
        yesterday = today - timedelta(days=1)
        
        domain = [
            ('state', 'in', ['purchase', 'done']),
            ('payment_date', 'in', [today, yesterday])
        ]
        
        orders = self.search(domain)
        
        missing_orders_info = []
        for order in orders:
            has_ppd = any(line.payment_method == 'PPD' for line in order.payment_documentation_line_ids)
            if not has_ppd:
                continue
                
            regular_pay_lines = order.payment_documentation_line_ids.filtered(lambda l: l.payment_method == 'regular_pay')
            regular_pay_sum = sum(regular_pay_lines.mapped('amount'))
            
            balance_to_cover = order.amount_total - regular_pay_sum
            
            if balance_to_cover > 0:
                missing_orders_info.append({
                    'order': order,
                    'balance_to_cover': balance_to_cover
                })
        
        if not missing_orders_info:
            return
            
        company = self.env.company
        notification_users = company.ppd_notification_user_ids
        
        if not notification_users:
            return
            
        template = self.env.ref('san_mex_company_custom.email_template_ppd_missing_reminder', raise_if_not_found=False)
        if not template:
            return
            
        for user in notification_users:
            template.with_context(missing_ppd_orders_info=missing_orders_info).send_mail(
                user.id, force_send=False
            )
