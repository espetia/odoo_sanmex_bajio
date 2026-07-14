# -*- coding: utf-8 -*-

from odoo import models, fields, api, _


class MyAccountPaymentRegister(models.TransientModel):
    _inherit = 'account.payment.register'

    analytic_account_id = fields.Many2one('account.analytic.account', string='Analytic Account')
    analytic_tag_ids = fields.Many2many('account.analytic.tag', string='Analytic Tags')

    @api.onchange("line_ids")
    def get_analytic(self):
        if self.line_ids:
            self.analytic_account_id=self.line_ids[0].move_id.analytic_account_id.id

    def _create_payment_vals_from_wizard(self):
        result = super(MyAccountPaymentRegister, self)._create_payment_vals_from_wizard()
        if self.analytic_account_id:
            result.update({
                'analytic_account_id': self.analytic_account_id.id
            })
        if self.analytic_tag_ids:
            result.update({
                'analytic_tag_ids':[(6, 0, self.analytic_tag_ids.ids)]
            })
        return result

    def _create_payment_vals_from_batch(self, batch_result):
        result = super(MyAccountPaymentRegister, self)._create_payment_vals_from_batch(batch_result=batch_result)
        tags = [tag.id for tag in self.analytic_tag_ids]
        if self.analytic_account_id:
            result.update({
                'analytic_account_id':self.analytic_account_id.id
            })
        if self.analytic_tag_ids:
            result.update({
                'analytic_tag_ids': [(6,0,self.analytic_tag_ids.ids)]
            })
        return result
