# -*- coding: utf-8 -*-
###############################################################################
#
#	Copyright (c) All rights reserved:
#		(c) 2024  account_invoice_due.py
#   By Jorge Chuc
#
#	This program is free software: you can redistribute it and/or modify
#	it under the terms of the GNU Affero General Public License as
#	published by the Free Software Foundation, either version 3 of the
#	License, or (at your option) any later version.
#
#	This program is distributed in the hope that it will be useful,
#	but WITHOUT ANY WARRANTY; without even the implied warranty of
#	MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
#	GNU Affero General Public License for more details.
#
#	You should have received a copy of the GNU Affero General Public License
#	along with this program.  If not, see http://www.gnu.org/licenses
#	
#	Odoo and OpenERP is trademark of Odoo S.A.
#
###############################################################################

from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError

class AccountDueReport(models.Model):
    _name = 'account.due.report'
    _description = 'Invoice Report'
    _auto = False
    _rec_name = 'invoice_date'
    _order = 'invoice_date desc'

    move_id = fields.Many2one('account.move', string='Factura')
    journal_id = fields.Many2one('account.journal', string='Diario', readonly=True)
    partner_id = fields.Many2one('res.partner', string='Cliente',readonly=True)
    company_id = fields.Many2one('res.company', string='Empresa', readonly=True)
    totalinvoice = fields.Float('Total Facturado')
    amount_residual = fields.Float('Total Vencido')
    invoice_date = fields.Date('Fecha de Factura')
    tota_due_30 = fields.Float('0-30 días')
    tota_due_60 = fields.Float('31-60 días')
    tota_due_90 = fields.Float('61-90 días')
    tota_due_more = fields.Float('91 o mas días')

    _depends ={
         'account.move': ['name','move_type', 'invoice_date', 'amount_residual', 'journal_id', 'partner_id', 'company_id','id','payment_state'],
         'res.partner':['name'],
    }


    @property
    def _table_query(self):
        return '%s %s %s %s' % (self._select(), self._from(), self._where(), self._group_by())
    
    @api.model
    def _select(self):
        return '''
            SELECT mv.id,
            mv.id as move_id,
            mv.amount_residual,
            mv.partner_id, mv.company_id,
            sum(mv.amount_total) as totalinvoice,
            mv.invoice_date,mv.journal_id,
            (COALESCE(case when current_date - mv.invoice_date between 0 and 30 then(mv.amount_residual) else 0 end)) as "tota_due_30",
            (COALESCE(case when current_date - mv.invoice_date between 31 and 60 then(mv.amount_residual) else 0 end)) as "tota_due_60",
            (COALESCE(case when current_date - mv.invoice_date between 61 and 90 then(mv.amount_residual) else 0 end)) as "tota_due_90",
            (COALESCE(case when current_date - mv.invoice_date between 91 and 3650 then(mv.amount_residual) else 0 end)) as "tota_due_more"
        '''


    @api.model
    def _from(self):
            return '''
                FROM ACCOUNT_MOVE mv
                '''
    @api.model
    def _where(self):
        return '''
                WHERE mv.payment_state in ('not_paid','partial') and mv.STATE NOT IN ('cancel','draft') and mv.move_type in ('out_invoice')
            '''
    @api.model
    def _group_by(self):
        return '''
                group by mv.partner_id, mv.invoice_date, mv.amount_residual, mv.journal_id, mv.company_id, mv.id
        '''