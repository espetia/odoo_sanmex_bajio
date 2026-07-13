# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import UserError
from datetime import datetime
from dateutil.relativedelta import relativedelta
import time
import logging
_logger = logging.getLogger(__name__)

# Fiscal Year
class AccountFiscal(models.Model):
    _name = "account.fiscal"
   
    

    name = fields.Char(required=True, index=True)
    code = fields.Char(string='Code',size=64, required=True, index=True)
    company_id = fields.Many2one('res.company', string='Company', required=True,
                default=lambda self: self.env['res.company']._company_default_get('account.account'))
    date_start = fields.Date(string='Date Start', required=True, states={'done': [('readonly', True)]}, index=True, default=fields.Date.context_today)
    date_stop  = fields.Date(string='Date End'  , required=True, states={'done': [('readonly', True)]}, index=True, default=fields.Date.context_today)
    period_ids = fields.One2many('account.period', 'fiscalyear_id', 'Periods')
    cierre = fields.Boolean('Cierre')
    state = fields.Selection([
            ('draft','Open'),
            ('done', 'Closed'),
        ], string='Status', index=True, readonly=True, default='draft')
        

    _order = "name, date_start" 

    

               


# Account Period
class AccountPeriod(models.Model):
    _name = "account.period"
    _description = "Account Periods - Dummy"
    
    #@api.model
    @api.depends('name')
    def _get_name2(self):
        for rec in self:
            rec.name2 = rec.name[-4:]+ '-' + rec.name[:2]
    
    fiscalyear_id =  fields.Many2one('account.fiscal', string='Fiscal Year', required=True, states={'done':[('readonly',True)]})
    name = fields.Char(string='Period Name', required=True, index=True)
    name2 = fields.Char(compute='_get_name2' ,string='Period Name', store=True)
    special = fields.Boolean(string='Closing Period', required=False)
    code = fields.Char(string='Code',size=64, required=True, index=True)
    company_id = fields.Many2one('res.company', string='Company', required=True,
                default=lambda self: self.env['res.company']._company_default_get('account.account'))
    date_start = fields.Date(string='Date Start', required=True, states={'done': [('readonly', True)]}, index=True, default=fields.Date.context_today)
    date_stop  = fields.Date(string='Date End'  , required=True, states={'done': [('readonly', True)]}, index=True, default=fields.Date.context_today)
    state = fields.Selection([
            ('draft','Open'),
            ('done', 'Closed'),
        ], string='Status', index=True, readonly=True, default='draft',
        copy=False,
        help=" * The 'Open' status is for Open Periods. If Period is open \nthen you can add / upate records (Account entries, Invoices, etc.)\n\n"
             " * The 'Done' status is used to restrict modification of any information related to this Period")

    _order = "date_start, special desc"

    _sql_constraints = [
        ('code_company_uniq', 'unique (code,company_id)', 'The code of the account must be unique per company !')
    ]

    

    
# Close Account Period Wizard
class AccountPeriodClose(models.TransientModel):
    """
        close period
    """
    _name = "account.period.close"
    _description = "period close"

    sure = fields.Boolean(string='Check this box')


    

