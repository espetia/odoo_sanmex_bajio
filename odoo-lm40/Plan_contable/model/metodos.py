# -*- coding: utf-8 -*-

from odoo.exceptions import UserError, ValidationError
from odoo import api, fields, models, _



class AccountMoveLine(models.Model):
    _inherit = "account.move.line"    
    
    @api.model
    def _query_get2(self):
        obj='l'
        fiscalyear_obj = self.env['account.fiscal']
        fiscalperiod_obj = self.env['account.period']
        account_obj = self.env['account.account']
        fiscalyear_ids = []
        context = self._context.copy()
        initial_bal = context.get('initial_bal', False)
        company_clause = " "
        if context.get('company_id', False):
            
            if context.get('revaluation', False):
                company_clause = " AND " +obj+".company_id = %s" % context.get('company_id', False)
            else:
                company_clause = " AND " +obj+".company_id in %s" % tuple([x.id for x in self.env.user.company_ids])
        if not context.get('fiscalyear', False):
            if context.get('all_fiscalyear', False):
                
                fiscalyear_ids = [x.id for x in fiscalyear_obj.search([])]
            else:
                
                if context.get('revaluation', False):
                    fiscalyear_ids = [x.id for x in fiscalyear_obj.search([('state', '=', 'draft'),('company_id','=',self.env.user.company_id.id)])]
                else:
                    fiscalyear_ids = [x.id for x in fiscalyear_obj.search([('state', '=', 'draft')])]
        else:
                        
            if context.get('revaluation', False):
                fiscalyear_ids = [context['fiscalyear']]
            else:
                self._cr.execute("select name from account_fiscalyear where id in (%s) limit 1" % ((','.join([str(x) for x in [context['fiscalyear']]])) or '0'))
                ydata = self._cr.fetchone()
                fiscalyear_name = ydata[0] or ''
                companies = [x.id for x in self.env.user.company_ids]
                fiscalyear_ids = [x.id for x in fiscalyear_obj.search([('company_id','in', tuple(companies),), ('name','=', fiscalyear_name)])]

        fiscalyear_clause = (','.join([str(x) for x in fiscalyear_ids])) or '0'
        state = context.get('state', False)
        where_move_state = ''
        where_move_lines_by_date = ''

        if context.get('date_from', False) and context.get('date_to', False):
            if initial_bal:
                where_move_lines_by_date = " AND " +obj+".move_id IN (SELECT id FROM account_move WHERE date < '" + context['date_from']+"')"
            else:
                where_move_lines_by_date = " AND " +obj+".move_id IN (SELECT id FROM account_move WHERE date >= '" + context['date_from']+"' AND date <= '" + context['date_to']+"')"

        if state:
            if state.lower() not in ['all']:
                where_move_state= " AND "+obj+".move_id IN (SELECT id FROM account_move WHERE account_move.state = '"+state+"')"
        if context.get('period_from', False) and context.get('period_to', False) and not context.get('periods', False):
            if initial_bal:
                period_company_id = fiscalperiod_obj.browse(context['period_from']).company_id.id
                first_period = fiscalperiod_obj.search([('company_id', '=', period_company_id)], order='date_start', limit=1)[0]
                context['periods'] = fiscalperiod_obj.build_ctx_periods(first_period, context['period_from'])
            else:
                context['periods'] = fiscalperiod_obj.build_ctx_periods(context['period_from'], context['period_to'])
        if context.get('periods', False):
            xperiods = fiscalperiod_obj.search([('id','in', context['periods'])])
            xperiods = [x.name for x in xperiods]
            context['periods'] = [x.id for x in fiscalperiod_obj.search([('name','in',(tuple(xperiods,)))])]
            
            if initial_bal:
                query = obj+".period_id IN (SELECT id FROM account_period WHERE fiscalyear_id IN (%s)) %s %s" % (fiscalyear_clause, where_move_state, where_move_lines_by_date)
                period_ids = fiscalperiod_obj.search([('id', 'in', context['periods'])], order='date_start', limit=1)
                if period_ids and period_ids[0]:
                    first_period = fiscalperiod_obj.browse(period_ids[0])
                    ids = ','.join([str(x) for x in context['periods']])
                    query = obj+".period_id IN (SELECT id FROM account_period WHERE fiscalyear_id IN (%s) AND date_start <= '%s' AND id NOT IN (%s)) %s %s" % (fiscalyear_clause, first_period.date_start, ids, where_move_state, where_move_lines_by_date)
            else:
                ids = ','.join([str(x) for x in context['periods']])
                query = obj+".period_id IN (SELECT id FROM account_period WHERE fiscalyear_id IN (%s) AND id IN (%s)) %s %s" % (fiscalyear_clause, ids, where_move_state, where_move_lines_by_date)
        else:
            query = obj+".period_id IN (SELECT id FROM account_period WHERE fiscalyear_id IN (%s)) %s %s" % (fiscalyear_clause, where_move_state, where_move_lines_by_date)

        if initial_bal and not context.get('periods', False) and not where_move_lines_by_date:
            
            raise UserError(_('You have not supplied enough arguments to compute the initial balance, please select a period and a journal in the context.'))


        if context.get('journal_ids', False):
            query += ' AND '+obj+'.journal_id IN (%s)' % ','.join(map(str, context['journal_ids']))

        if context.get('chart_account_id', False):
            child_ids = account_obj._get_children_and_consol([context['chart_account_id']])
            query += ' AND '+obj+'.account_id IN (%s)' % ','.join(map(str, child_ids))

        query += company_clause
        return query
        
        

        
class AccountAccount(models.Model):
    _inherit = "account.account"

    
    def __compute(self):
        
        query=''
        query_params=()
        mapping = {
            'balance': "COALESCE(SUM(l.debit),0) - COALESCE(SUM(l.credit), 0) as balance",
            'debit': "COALESCE(SUM(l.debit), 0) as debit",
            'credit': "COALESCE(SUM(l.credit), 0) as credit",
            
        }
        
        children_and_consolidated = self._get_children_and_consol(self._ids)
        
        res = {}
        if children_and_consolidated:
            aml_query = self.env['account.move.line']._query_get2()
            wheres = [""]
            if query.strip():
                wheres.append(query.strip())
            if aml_query.strip():
                wheres.append(aml_query.strip())
            filters = " AND ".join(wheres)
            
            
            request = ("SELECT " +\
                       ', '.join(mapping.values()) +
                       " FROM account_move_line l" \
                       " WHERE l.account_id IN %s " \
                            + filters +
                       " ")
            params = (tuple(children_and_consolidated),) + query_params
            self._cr.execute(request, params)
            res = self._cr.dictfetchall()[0]
            sign = self.browse(self._ids)[0]['sing_1']
            res.update({'balance':res['balance']*sign})
        return res
    
    


        
        

    
            
        
        
