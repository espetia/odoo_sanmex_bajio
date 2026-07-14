# -*- coding: utf-8 -*-

import logging
from odoo import models, fields, api

_logger = logging.getLogger(__name__)


class AccountPaymentRegister(models.TransientModel):
    _inherit = 'account.payment.register'

    @api.onchange('line_ids')
    def get_analytic(self):
        _logger.info("Executing onchange get_analytic method in AccountPaymentRegister")
        if self.line_ids:
            _logger.info("onchange get_analytic: line_ids found")
            move = self.line_ids[0].move_id
            if move.invoice_line_ids:
                _logger.info("onchange get_analytic: Invoice has line IDs")
                for line in move.invoice_line_ids:
                    if line.analytic_account_id:
                        _logger.info(f"onchange get_analytic: Found analytic account ID {line.analytic_account_id.id} in line {line.id}")
                        self.analytic_account_id = line.analytic_account_id.id
                        break
            else:
                _logger.info("onchange get_analytic: Invoice does not have line IDs")
        else:
            _logger.info("onchange get_analytic: No line_ids found")
