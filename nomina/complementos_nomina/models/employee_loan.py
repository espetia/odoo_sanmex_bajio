# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import ValidationError
from datetime import datetime

class EmployeeLoan(models.Model):
    _inherit = 'employee.loan'

    payroll_number_employee = fields.Char(string="Payroll number employee", related="employee_id.no_empleado")

    @api.model
    def default_get(self, fields):
        res = super(EmployeeLoan, self).default_get(fields)
        res['term'] = 1
        return res

    @api.constrains('employee_id')
    def _check_loan(self):
        now = datetime.now()
        year = now.year
        s_date = str(year) + '-01-01'
        e_date = str(year) + '-12-01'

        loan_ids = self.search(
            [('employee_id', '=', self.employee_id.id), ('date', '<=', e_date), ('date', '>=', s_date)])
        loan = len(loan_ids)
        if loan > self.employee_id.loan_request:
            print("Puedes crear un máximo de %s de prestamo", self.employee_id.loan_request)
            #raise ValidationError("Puedes crear un máximo de %s de prestamo" % self.employee_id.loan_request)

    @api.depends('remaing_amount')
    def is_ready_to_close(self):
        for loan in self:
            if loan.state == 'done':
                if loan.remaing_amount <= 0:
                    loan.is_close = True
                else:
                    #loan.is_close = False
                    loan.is_close = True
            else:
                loan.is_close = False
                
    @api.depends('start_date', 'term')
    def _get_end_date(self):
        for loan in self:
            if loan.start_date and loan.loan_type_id:
                periodo_de_pago = self.loan_type_id.periodo_de_pago or ''
                start_date = self.start_date

                if periodo_de_pago == 'Semanal':
                    end_date = start_date + relativedelta(weeks=self.term) - relativedelta(days=1)
                elif periodo_de_pago == 'Quincenal':
                    end_date = self.get_quincenal_end_date(start_date, loan.term)
                else:
                    end_date = start_date + relativedelta(months=self.term)

                loan.end_date = end_date.strftime("%Y-%m-%d")
            else:
                loan.end_date = datetime.today().strftime("%Y-%m-%d")
