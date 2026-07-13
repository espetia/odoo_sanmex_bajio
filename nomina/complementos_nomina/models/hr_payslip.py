# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, models, fields

class HrPayslipRun(models.Model):
    _inherit = 'hr.payslip'

    no_empleado = fields.Char(related='employee_id.no_empleado', string='Número de empleado', readonly=True, store=True)
    acum_incap_inte = fields.Float('Percepciones gravadas', compute='_get_acumulados_mensual')
    resumen = fields.Char(string='Resumen', copy=False)

    @api.onchange('mes', 'periodicidad_pago', 'no_periodo')
    def _get_acumulados_mensual(self):
        self.acum_sueldo = self.acumulado_mes('P001')
        self.acum_per_totales = self.acumulado_mes('TPER')
        # self.acum_fondo_ahorro = acumulado_mes('P001')
        self.acum_subsidio_aplicado = self.acumulado_mes('SUB')
        self.acum_isr_antes_subem = self.acumulado_mes('ISR')
        self.acum_per_grav = self.acumulado_mes('TPERG') - self.acumulado_mes('D103')
        self.acum_isr = self.acumulado_mes('ISR2')
        self.acum_incap_inte = self.acumulado_mes('D103')

    def acumulado_mes(self, codigo):
        total = 0
        if self.employee_id and self.mes and self.contract_id.tablas_cfdi_id:
            if self.periodicidad_pago == '04':
               mes_actual = self.contract_id.tablas_cfdi_id.tabla_mensual.search([('dia_inicio', '<=', self.date_from),('dia_fin', '>=', self.date_to)],limit =1)
            else:
               mes_actual = self.contract_id.tablas_cfdi_id.tabla_semanal.search([('no_periodo', '=', self.no_periodo)],limit =1)
            date_start = mes_actual.dia_inicio # self.date_from
            date_end = mes_actual.dia_fin #self.date_to
            domain=[('state','=', 'done')]
            if date_start:
                domain.append(('date_from','>=',date_start))
            if date_end:
                domain.append(('date_to','<=',date_end))
            domain.append(('employee_id','=',self.employee_id.id))

            domain.append(('estado_factura', '!=', 'factura_cancelada'))

            if not self.contract_id.calc_isr_extra:
               domain.append(('tipo_nomina','=','O'))
            rules = self.env['hr.salary.rule'].search([('code', '=', codigo)])
            payslips = self.env['hr.payslip'].search(domain)
            payslip_lines = payslips.mapped('line_ids').filtered(lambda x: x.salary_rule_id.id in rules.ids)
            employees = {}
            for line in payslip_lines:
                if line.slip_id.employee_id not in employees:
                    employees[line.slip_id.employee_id] = {line.slip_id: []}
                if line.slip_id not in employees[line.slip_id.employee_id]:
                    employees[line.slip_id.employee_id].update({line.slip_id: []})
                employees[line.slip_id.employee_id][line.slip_id].append(line)

            for employee, payslips in employees.items():
                for payslip,lines in payslips.items():
                    for line in lines:
                        total += line.total
        return total

    def generar_resumen(self, grabar=True):
        reglas = {}
        for line in self.line_ids:
            reglas[line.code] = line.total
        resumen = {self.employee_id.no_empleado: reglas}
        if grabar:
            self.write({'resumen': resumen})
        return resumen