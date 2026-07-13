# -*- coding: utf-8 -*-

from odoo import api, fields, models, tools, _

class HrPayslipInput(models.Model):
    _inherit = 'hr.payslip.input'

    salary_rule_id = fields.Many2one(comodel_name="hr.salary.rule", string="Salary rule")

    @api.onchange('salary_rule_id')
    def _onchange_salary_rule_id(self):
        self.name = self.salary_rule_id.name
        self.code = self.salary_rule_id.code