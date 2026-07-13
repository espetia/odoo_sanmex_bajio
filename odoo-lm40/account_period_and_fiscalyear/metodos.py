# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import UserError
#from datetime import datetime
from dateutil.relativedelta import relativedelta
import time
import datetime
import logging
_logger = logging.getLogger(__name__)


# Fiscal Year
class AccountFiscal(models.Model):
    _inherit = "account.fiscal"

    @api.model
    @api.constrains('date_start', 'date_stop')
    def _check_duration(self):        
        if self.date_stop < self.date_start:
            raise UserError(_('Error!\nThe start date of a fiscal year must precede its end date.'))
    
    
    def create_period(self):       
        interval = 1
        period_obj = self.env['account.period'] 
        #año_fiscal = self.env['account.fiscal'].browse(self._context['uid'])
        #_logger.error('fy: %s', año_fiscal.name)     
        #self.ensure_one()
        _logger.error('conexto: %s', self._context)
        for record in self:
            _logger.error('fy: %s', record.id)
            ds = datetime.datetime.strptime(str(record.date_start), '%Y-%m-%d').date()
            _logger.error('ds: %s', ds)
            period_obj.create({
                    'name':  "%s%s" % ('00/', ds.strftime('%Y')),
                    'code': ds.strftime('00/%Y'),
                    'date_start': ds,
                    'date_stop': ds,
                    'special': True,
                    'company_id': self.company_id.id,
                    'fiscalyear_id': record.id,
                })
            _logger.error('period_obj: %s', period_obj)
            while str(ds.strftime('%Y-%m-%d')) < str(record.date_stop):
                de = ds + relativedelta(months=interval, days=-1)

                if str(de.strftime('%Y-%m-%d')) > str(record.date_stop):
                    de = datetime.strptime(record.date_stop, '%Y-%m-%d')

                period_obj.create({
                    'name': ds.strftime('%m/%Y'),
                    'code': ds.strftime('%m/%Y'),
                    'date_start': ds.strftime('%Y-%m-%d'),
                    'date_stop': de.strftime('%Y-%m-%d'),
                    'company_id': self.company_id.id,
                    'fiscalyear_id': record.id,
                })
                
                ds = ds + relativedelta(months=interval)
        return True 
        

    

    

    #@api.model
    def find(self, dt=None, exception=True):
        res = self.finds(dt, exception)
        return res and res[0] or False

    #@api.model
    def finds(self, dt=None, exception=True):
        if not dt:
            dt = fields.Date.context_today(self)
        args = [('date_start', '<=' ,dt), ('date_stop', '>=', dt)]        
        if self._context.get('company_id', False):
            company_id = self._context['company_id']
        else:
            company_id = self.env.user.company_id.id
        args.append(('company_id', '=', company_id))
        ids = [x.id for x in self.search(args)]
        
        return ids


# Account Period
class AccountPeriod(models.Model):
    _inherit = "account.period"
 
    #@api.model
    @api.constrains('date_start', 'date_stop')
    def _check_duration(self):        
        if self.date_stop < self.date_start:
            raise UserError(_('Error!\nThe start date of this Period must precede its end date.'))


    #@api.model
    @api.constrains('date_start', 'date_stop')            
    def _check_year_limit(self):
        if self.special:
            return
        
        if self.fiscalyear_id.date_stop < self.date_stop or \
           self.fiscalyear_id.date_stop < self.date_start or \
           self.fiscalyear_id.date_start > self.date_start or \
           self.fiscalyear_id.date_start > self.date_stop:
            raise UserError(_('Error!\nThe period is invalid. Either some periods are overlapping or the period\'s dates are not matching the scope of the fiscal year.'))
        pids = self.search([('date_stop','>=',self.date_start),('date_start','<=',self.date_stop),('special','=',False),('id','<>',self.id) ,('company_id','=',self.fiscalyear_id.company_id.id)])
        for period in self.browse(pids):
            if period.fiscalyear_id.company_id.id==self.fiscalyear_id.company_id.id:
                raise UserError(_('Error!\nThe period is invalid. Either some periods are overlapping or the period\'s dates are not matching the scope of the fiscal year.'))
        return

    @api.returns('self')
    def next(self, period, step):
        ids = self.search([('date_start','>',period.date_start)])
        if len(ids)>=step:
            return ids[step-1]
        return False

    @api.returns('self')
    def find(self, dt=None):
        
        if not dt:
            dt = fields.Date.context_today(self)
        args = [('date_start', '<=' ,dt), ('date_stop', '>=', dt)]
        if self._context.get('company_id', False):
            args.append(('company_id', '=', self._context['company_id']))
        else:
            args.append(('company_id', '=', self.env.user.company_id.id))
        result = []
        if self._context.get('account_period_prefer_normal', True):
            # look for non-special periods first, and fallback to all if no result is found
            result = self.search(args + [('special', '=', False)])
        if not result:
            result = self.search(args)
        if not result:
            model, action_id = self.env['ir.model.data'].get_object_reference('account', 'action_account_period')
            msg = _('There is no period defined for this date: %s.\nPlease go to Configuration/Periods.') % dt
            raise UserError(msg + _('Go to the configuration panel'))
        return result

    #@api.model
    def action_draft(self):
        mode = 'draft'
        for period in self.browse():
            if period.fiscalyear_id.state == 'done':
                raise UserError(_('You can not re-open a period which belongs to closed fiscal year.'))        
        self._cr.execute('update account_period set state=%s where id in %s', (mode, tuple(self._ids),))
        self.invalidate_cache()
        return True



    #@api.model
    def write(self, vals):
        if 'company_id' in vals:
            move_lines = self.env['account.move.line'].search([('period_id', 'in', self._ids)])
            if move_lines:
                raise UserError(_('This journal already contains items for this period, therefore you cannot modify its company field.'))
        return super(AccountPeriod, self).write(vals)

    def build_ctx_periods(self, period_from_id, period_to_id):
        if period_from_id == period_to_id:
            return [period_from_id]
        period_from = self.browse(period_from_id)
        period_date_start = period_from.date_start
        company1_id = period_from.company_id.id
        period_to = self.browse(period_to_id)
        period_date_stop = period_to.date_stop
        company2_id = period_to.company_id.id
        if company1_id != company2_id:
            raise UserError(_('You should choose the periods that belong to the same company.'))
        if period_date_start > period_date_stop:
            raise UserError(_('Start period should precede then end period.'))
        
        if period_from.special:
            return [x.id for x in self.search([('date_start', '>=', period_date_start), ('date_stop', '<=', period_date_stop)])]
        return [x.id for x in self.search([('date_start', '>=', period_date_start), ('date_stop', '<=', period_date_stop), ('special', '=', False)])]

    
# Close Account Period Wizard
class AccountPeriodClose(models.TransientModel):
    """
        close period
    """
    _inherit = "account.period.close"

    #@api.model
    def data_save(self):
        """
        This function close period
         """
        context = dict(self._context or {})
        account_move_obj = self.env['account.move']        
        mode = 'done'
        if self.sure:
            for id in context['active_ids']:                
                self._cr.execute('update account_period set state=%s where id=%s', (mode, id))
                self.invalidate_cache()

        return {'type': 'ir.actions.act_window_close'}
    






