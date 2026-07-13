# -*- encoding: utf-8 -*-
from odoo import api, fields, models, tools
import logging
_logger = logging.getLogger(__name__)


class Currency(models.Model):
    _inherit = "res.currency"

    rate_custom = fields.Float(compute='_compute_current_rate_custom', string='Tasa Normal', digits=(12, 6),  help='The rate of the currency to the currency of rate 1.')

    @api.model
    def _compute_current_rate_custom(self):
        date = self._context.get('date') or fields.Date.today()
        company_id = self._context.get('company_id') or self.env.user.company_id.id 
        _logger.error('company_id: %s', company_id)
        # the subquery selects the last rate before 'date' for the given currency/company
        query = """SELECT c.id, (SELECT r.rate_custom FROM res_currency_rate r
                                  WHERE r.currency_id = c.id AND r.name <= %s
                                    AND (r.company_id IS NULL OR r.company_id = %s)
                               ORDER BY r.company_id, r.name DESC
                                  LIMIT 1) AS rate
                   FROM res_currency c
                   WHERE c.id IN %s"""
        
        self._cr.execute(query, (date, company_id, tuple(self.ids)))
        _logger.error("edvregty: %s", self._cr.execute(query, (date, company_id, tuple(self.ids))))
        currency_rates = dict(self._cr.fetchall())
        _logger.error('currency_rates: %s', currency_rates)
        for currency in self:
            currency.rate_custom = currency_rates.get(currency.id) or 1.0
            _logger.error("currenenfcnfrhnc: %s", currency.rate_custom)
    
    def update_tasa_custom(self):
        for rate in self.rate_ids:
            rate.rate_custom = 1 / (rate.rate and rate.rate or 1.0)
        

class CurrencyRate(models.Model):
    _inherit = "res.currency.rate"

    rate_custom = fields.Float(digits=(12, 6), help='Ratio invertido')

    @api.onchange('rate_custom')
    def _onchange_rate_custom(self):
        self.rate = 1 / (self.rate_custom and self.rate_custom or 1)