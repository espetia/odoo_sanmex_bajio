# -*- encoding: utf-8 -*-

from odoo import models, fields

class ContractHistorialSalario(models.Model):
    _inherit = 'contract.historial.salario'

    department_employee = fields.Char(string="Department", related="contract_id.employee_id.department_id.name", store=True)
    position_employee = fields.Char(string="Position", related="contract_id.employee_id.job_id.name", store=True)