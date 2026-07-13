# -*- coding:utf-8 -*-

from odoo import api, fields, models


class HrPayslipRun(models.Model):
    _inherit = 'hr.payslip'

    no_empleado = fields.Char(related='employee_id.no_empleado', string='Número de empleado')