# -*- coding: utf-8 -*-

import time
from odoo import api, fields, models, _
from odoo.exceptions import UserError
import logging
_logger = logging.getLogger(__name__)

#----------------------------------------------------------
# Account Move
#----------------------------------------------------------

class AccountMove(models.Model):
    _inherit = "account.move"

    item_concept = fields.Char(string='Concepto', size=300)

    @api.model
    def _check_fiscalyear_lock_date(self): #_check_fiscalyear_lock_date
        res = super(AccountMove, self)._check_fiscalyear_lock_date()
        for move in self:
            if move.period_id.state == 'done':
                raise UserError(_("You cannot add/modify entries in Closed Period %s. Check the Period state" % (move.period_id.name)))
        return res

    #@api.model    
    @api.depends('closing_period','date','company_id')
    def _compute_period(self):        
        for move in self:
            #self._cr.execute("select id from account_period where '%s' between date_start and date_stop and special=%s and company_id=%s;" % (move.date, move.closing_period and 'true' or 'false', move.company_id.id or self.env.user.company_id.id))
            periodos = self.env['account.period'].search([('date_start', '<=', move.date), ('date_stop', '>=', move.date), ('company_id', '=', self.env.user.company_id.id),('special','=',False)])
            _logger.error('periodos_1: %s', periodos)
            move.period_id = periodos
        
            
    
    period_id = fields.Many2one('account.period', string='Period', readonly=True, required=False,
                compute='_compute_period', store=True)            
    closing_period = fields.Boolean(string="En Periodo de Cierre", default=False)

    
    @api.model
    @api.constrains('closing_period','date')
    def _check_closing_period_and_date(self):
        period_obj = self.env['account.period']
        for move in self:
            if move.closing_period:
                period = period_obj.search([('special','=', True),('date_start', '>=', move.date), ('date_stop', '<=', move.date)], limit=1)
                if not period:
                    raise ValueError(_('Warning !!!\n\nYou have no Closing Period matching Account Move Date'))
        
    
#----------------------------------------------------------
# Account Move Line
#----------------------------------------------------------

class AccountMoveLine(models.Model):
    _inherit = "account.move.line"


    period_id = fields.Many2one('account.period', string='Period', related='move_id.period_id',
                                store=True, readonly=True, copy=False)