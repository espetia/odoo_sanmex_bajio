# -*- coding: utf-8 -*-
from odoo import models, api, _
from dateutil.relativedelta import relativedelta
from odoo.fields import Date

class SaleOrder(models.Model):
    _inherit = 'sale.order'

    @api.onchange('partner_id')
    def _onchange_partner_id_debtor_warning(self):
        if not self.partner_id:
            return

        two_months_ago = Date.context_today(self) - relativedelta(months=2)
        domain = [
            ('partner_id', '=', self.partner_id.id),
            ('move_type', '=', 'out_invoice'),
            ('state', '=', 'posted'),
            ('payment_state', '=', 'not_paid'),
            ('invoice_date_due', '<=', two_months_ago)
        ]
        
        debtor_invoices = self.env['account.move'].search(domain, limit=1)
        if debtor_invoices:
            return {
                'warning': {
                    'title': _("¡Atención!"),
                    'message': _("El cliente seleccionado es un deudor con facturas vencidas por más de 2 meses.")
                }
            }
