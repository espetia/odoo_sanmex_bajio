# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
from datetime import datetime, timedelta

class CustomerStatusLog(models.Model):
    _name = 'customer.status.log'
    _description = 'Customer Status Log'
    _order = 'date_detected desc'

    partner_id = fields.Many2one('res.partner', string='Customer', required=True, ondelete='cascade')
    status_type = fields.Selection([
        ('new', 'New Customer'),
        ('recovered', 'Recovered Customer')
    ], string='Status Type', required=True)
    date_detected = fields.Datetime(string='Date Detected', default=fields.Datetime.now, required=True)
    invoice_id = fields.Many2one('account.move', string='Trigger Invoice', help="The invoice that triggered this status change.")
    analytic_account_names = fields.Char(
        string='Cuentas Analíticas',
        compute='_compute_analytic_account_names',
    )

    @api.depends('invoice_id.invoice_line_ids.analytic_account_id')
    def _compute_analytic_account_names(self):
        for rec in self:
            accounts = rec.invoice_id.invoice_line_ids.analytic_account_id
            rec.analytic_account_names = ', '.join(accounts.mapped('name'))

    @api.model
    def get_stats(self):
        """Returns statistics for the KPI dashboard."""
        today = fields.Date.today()
        first_day_month = today.replace(day=1)
        
        # New Customers (This Month)
        new_month_count = self.search_count([('status_type', '=', 'new'), ('date_detected', '>=', first_day_month)])
        # Recovered Customers (This Month)
        recovered_month_count = self.search_count([('status_type', '=', 'recovered'), ('date_detected', '>=', first_day_month)])
        # Total New Customers
        new_total_count = self.search_count([('status_type', '=', 'new')])
        # Total Recovered Customers
        recovered_total_count = self.search_count([('status_type', '=', 'recovered')])
        
        return {
            'new_month': new_month_count,
            'recovered_month': recovered_month_count,
            'new_total': new_total_count,
            'recovered_total': recovered_total_count,
        }

    @api.model
    def _check_customer_status_by_date(self, start_date):
        """Logic to detect new and recovered customers from a specific date."""
        # Find invoices from start_date to today
        new_posted_invoices = self.env['account.move'].search([
            ('move_type', '=', 'out_invoice'),
            ('state', '=', 'posted'),
            ('invoice_date', '>=', start_date)
        ], order='invoice_date asc')

        for invoice in new_posted_invoices:
            partner = invoice.partner_id
            if not partner:
                continue

            # Check if this invoice is already logged
            existing_log = self.search([('invoice_id', '=', invoice.id)], limit=1)
            if existing_log:
                continue

            # Check all posted invoices for this partner up to this invoice date
            # to determine if it's new or recovered at THAT point in time.
            all_invoices_until_now = self.env['account.move'].search([
                ('partner_id', '=', partner.id),
                ('move_type', '=', 'out_invoice'),
                ('state', '=', 'posted'),
                ('invoice_date', '<=', invoice.invoice_date)
            ], order='invoice_date asc')

            # We need to filter out invoices with the same date but later ID if necessary, 
            # but usually Odoo keeps them in order. 
            # Let's refine the list to include the current invoice and previous ones.
            
            invoices_list = all_invoices_until_now.ids
            current_index = invoices_list.index(invoice.id)
            
            previous_invoices = all_invoices_until_now[:current_index]
            
            if not previous_invoices:
                # 1. New Customer Logic: No previous posted invoices
                self.create({
                    'partner_id': partner.id,
                    'status_type': 'new',
                    'date_detected': fields.Datetime.to_datetime(invoice.invoice_date),
                    'invoice_id': invoice.id,
                })
            else:
                # 2. Recovered Customer Logic
                # Check the gap between this invoice and the immediately preceding one
                prev_invoice = previous_invoices[-1]
                
                if prev_invoice.invoice_date:
                    # Check gap > 6 months (approx 180 days)
                    gap = invoice.invoice_date - prev_invoice.invoice_date
                    if gap.days > 180:
                        self.create({
                            'partner_id': partner.id,
                            'status_type': 'recovered',
                            'date_detected': fields.Datetime.to_datetime(invoice.invoice_date),
                            'invoice_id': invoice.id,
                        })

    @api.model
    def _cron_check_customer_status(self):
        """Cron task to detect new and recovered customers daily."""
        yesterday = fields.Date.today() - timedelta(days=1)
        self._check_customer_status_by_date(yesterday)
