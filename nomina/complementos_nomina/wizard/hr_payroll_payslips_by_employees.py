# -*- coding: utf-8 -*-

from odoo import api, fields, models
import logging
_logger = logging.getLogger(__name__)

class HrPayslipEmployees(models.TransientModel):
    _inherit = 'hr.payslip.employees'

    fch_inicio = fields.Date(string='Fecha inicio')
    fch_fin = fields.Date(string='Fecha fin')
    periodicidad_pago = fields.Selection(
        selection=[('01', 'Diario'),
                   ('02', 'Semanal'),
                   ('03', 'Catorcenal'),
                   ('04', 'Quincenal'),
                   ('05', 'Mensual'),
                   ('06', 'Bimensual'),
                   ('07', 'Unidad obra'),
                   ('08', 'Comisión'),
                   ('09', 'Precio alzado'),
                   ('10', 'Pago por consignación'),
                   ('99', 'Otra periodicidad'), ],
        string='Periodicidad de pago CFDI',
    )

    @api.onchange('fch_inicio')
    def _onchange_fch_inicio(self):
        if not self.fch_inicio:
            payslip_run_id = self.env['hr.payslip.run'].search([('id', '=', self._context['active_id'])])
            self.fch_inicio = payslip_run_id.date_start
            self.fch_fin = payslip_run_id.date_end
            self.periodicidad_pago = payslip_run_id.periodicidad_pago

    @api.onchange('employee_ids', 'fch_fin')
    def _onchange_employee_ids(self):
        if self.periodicidad_pago and self.periodicidad_pago != '99':
            linea = []
            contract_ids = self.env['hr.contract'].search([
                ('fch_antiguedad', '<=', self.fch_fin),
                ('periodicidad_pago', '=', self.periodicidad_pago)
            ])
            for contract_id in contract_ids:
                if not contract_id.date_end:
                    if contract_id.employee_id.id not in linea:
                        linea.append(contract_id.employee_id.id)
                else:
                    if contract_id.date_end >= self.fch_fin:
                        if contract_id.employee_id.id not in linea:
                            linea.append(contract_id.employee_id.id)
            dynamic_domain = {'employee_ids': [('id', 'in', linea)]}
            return {'domain': dynamic_domain}
