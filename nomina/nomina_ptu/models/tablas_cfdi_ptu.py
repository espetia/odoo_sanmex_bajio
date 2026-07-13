# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import ValidationError
from odoo.exceptions import UserError
from datetime import datetime
from datetime import datetime, timedelta
import logging
_logger = logging.getLogger(__name__)

class TablasCFDI(models.Model):
    _inherit = 'tablas.cfdi'
    _description = 'TablasCFDI'

    ptu_cal = fields.Boolean('PTU Calculado')

    def calcular_reparto_utilidades(self):
        if self.ptu_cal == False:
            #payslips = self.env['hr.payslip'].search([('date_from', '>=', self.fecha_inicio), ('date_to', '<=', self.fecha_fin),('tipo_nomina','=', 'O'), ('state','=', 'done'), ('employee_id.regimen','=', '02'), ('estado_factura', '=', 'factura_correcta')])
            payslips = self.env['hr.contract'].search([('employee_id.regimen','=', '02'), ('state', 'in', ('open', 'close'))])
            _logger.error('nomina: %s', payslips)
            #work100_lines = payslips.mapped('worked_days_line_ids').filtered(lambda x:x.code=='WORK100')
            #net_lines = payslips.mapped('line_ids').filtered(lambda x:x.code=='NET')    
            total_dias_by_employee = {}
            total_sueldo_employee = {}
            fecha_fin = ""
            fecha_inicio = ""
            año_antiguedad = ""
            año_calculo = ""
            año_fin = ""
            año_calculo = ""
            total_dias_trabajados, total_sueldo_percibido = 0.0, 0.0
            for line in payslips:
                año_antiguedad = (line.fch_antiguedad).year
                año_calculo = (self.fecha_inicio).year
                if año_antiguedad < año_calculo:
                    fecha_inicio = self.fecha_inicio
                if año_antiguedad == año_calculo:
                    fecha_inicio = line.fch_antiguedad                
                if not line.date_end:

                    fecha_fin = self.fecha_fin
                else:
                    año_fin = (line.date_end).year
                    año_calculo = (self.fecha_fin).year
                    if año_fin > año_calculo:
                        fecha_fin = self.fecha_fin
                    if año_fin == año_calculo:
                        fecha_fin = line.date_end

                if año_antiguedad > año_calculo:
                    fecha_inicio = fecha_fin



                total_dias_trabajados += ((fecha_fin - fecha_inicio).days) + 1
                #_logger.error('días: %s', total_dias_trabajados)
                if line.employee_id not in total_dias_by_employee:
                    total_dias_by_employee.update({line.employee_id: 0.0})

                total_dias_by_employee[line.employee_id] = ((fecha_fin - fecha_inicio).days) + 1
                net_lines = self.env['contract.historial.salario'].search([('contract_id','=', line.id)])
                #_logger.error('salario: %s', net_lines)
                for lines in net_lines:

                    #total_sueldo_percibido += lines.sueldo_diario * total_dias_by_employee[line.employee_id]#total_dias_trabajados
                    #_logger.error('salario_percibido: %s', total_sueldo_percibido)
                    if lines.contract_id.employee_id not in total_sueldo_employee:
                        total_sueldo_employee.update({lines.contract_id.employee_id: 0.0})
                    if total_dias_by_employee[line.employee_id] < self.dias_min_trabajados:
                        total_sueldo_employee[lines.contract_id.employee_id] = 0.0
                    else:
                        total_sueldo_employee[lines.contract_id.employee_id] = lines.sueldo_diario * total_dias_by_employee[line.employee_id]#total_dias_trabajados
                    _logger.error('salario: %s', total_sueldo_employee[lines.contract_id.employee_id])
                total_sueldo_percibido += total_sueldo_employee[lines.contract_id.employee_id]
            employees = list(set(list(total_dias_by_employee.keys())  + list(total_sueldo_employee.keys())))
            _logger.error('empleado: %s', employees)

            for employee in employees:
                #employee.write({'dias_utilidad' : total_dias_by_employee.get(employee, 0.0), 'sueldo_utilidad' : total_sueldo_employee.get(employee,0.0)})
                vals = {
                    'empleado_id': employee_id.id,
                    'fecha_utilidad_inicio': self.fecha_inicio,
                    'fecha_utilidad_fin': self.fecha_fin,
                    'dias_utilidad' : total_dias_by_employee.get(employee, 0.0),
                    'sueldo_utilidad' : total_sueldo_employee.get(employee,0.0)
                    }
                self.env['tablas.utilidades'].create(vals)
                
            self.write({'total_dias_trabajados': total_dias_trabajados, 'total_sueldo_percibido':total_sueldo_percibido})
        else:
            raise UserError(_('El PTU ya ha sido Calculado'))
        
        return True

    def button_dummy(self):
        _logger.info('calculo de utilidades')
        self.calcular_reparto_utilidades()
        return True

class Employee(models.Model):
    _inherit = "hr.employee"

    utilidades_ids = fields.One2many('tablas.utilidades', 'empleado_id', string='Reparto de utilidades', readonly=True)


class TablasUilidades(models.Model):
    _name = 'tablas.utilidades'
    _description = 'Tablas Utilidades'

    empleado_id = fields.Many2one('hr.employee', string="Empleado")
    fecha_utilidad_inicio = fields.Date('Fecha Utilidad Inicio')
    fecha_utilidad_fin = fields.Date('Fecha Utilidad Fin')
    dias_utilidad = fields.Float('Dias para cálculo de Utilidad')
    sueldo_utilidad = fields.Float('Sueldo para cálculo de Utilidad')


class HrPayslipRun(models.Model):
    _inherit = 'hr.payslip.run'
    
    calcular_ptu = fields.Boolean('Calcular PTU')
    fecha_utilidad_inicio = fields.Date('Fecha Utilidad Inicio')
    fecha_utilidad_fin = fields.Date('Fecha Utilidad Fin')



class HrPayslipEmployeesExt(models.TransientModel):
    _inherit = 'hr.payslip.employees'
    
    def compute_sheet(self):
        payslips = self.env['hr.payslip']
        [data] = self.read()
        active_id = self.env.context.get('active_id')
        if active_id:
            [run_data] = self.env['hr.payslip.run'].browse(active_id).read(['date_start', 'date_end', 'credit_note'])
        from_date = run_data.get('date_start')
        to_date = run_data.get('date_end')
        if not data['employee_ids']:
            raise UserError(_("You must select employee(s) to generate payslip(s)."))
        payslip_batch = self.env['hr.payslip.run'].browse(active_id)
        struct_id = payslip_batch.estructura and payslip_batch.estructura.id or False
        other_inputs = []
        for other in payslip_batch.tabla_otras_entradas:
            if other.descripcion and other.codigo: 
                other_inputs.append((0,0,{'name':other.descripcion, 'code': other.codigo, 'amount':other.monto}))
        

              
        for employee in self.env['hr.employee'].browse(data['employee_ids']):
            slip_data = self.env['hr.payslip'].onchange_employee_id(from_date, to_date, employee.id, contract_id=False)
            _logger.error('datosparanomina: %s', slip_data)
            ptus = []
            if payslip_batch.calcular_ptu == True:
                dias = self.env['tablas.utilidades'].search([('fecha_utilidad_inicio', '>=', payslip_batch.fecha_utilidad_inicio), ('fecha_utilidad_fin', '<=', payslip_batch.fecha_utilidad_fin), ('empleado_id', '=', employee.id)])
                slip_data['value']['worked_days_line_ids'][0]['name'] = 'Reparto de utilidades días'
                slip_data['value']['worked_days_line_ids'][0]['code'] = 'PTUD'
                slip_data['value']['worked_days_line_ids'][0]['number_of_days'] = dias.dias_utilidad
                slip_data['value']['worked_days_line_ids'][0]['number_of_hours'] = 0
                
                slip_data['value']['worked_days_line_ids'].append({'name':'Reparto de utilidades sueldo', 'code': 'PTUS', 'number_of_days': 1.0, 'contract_id': slip_data['value'].get('contract_id')})

            res = {
                'employee_id': employee.id,
                'name': slip_data['value'].get('name'),
                'struct_id': struct_id or slip_data['value'].get('struct_id'),
                'contract_id': slip_data['value'].get('contract_id'),
                'payslip_run_id': active_id,
                'input_line_ids': [(0, 0, x) for x in slip_data['value'].get('input_line_ids')],
                'worked_days_line_ids': [(0, 0, x) for x in slip_data['value'].get('worked_days_line_ids')],
                'date_from': from_date,
                'date_to': to_date,
                'credit_note': run_data.get('credit_note'),
                'company_id': employee.company_id.id,
                #Added
                'tipo_nomina' : payslip_batch.tipo_nomina,
                'fecha_pago' : payslip_batch.fecha_pago,
                #'journal_id': payslip_batch.journal_id.id
            }
            if other_inputs and res.get('contract_id'):
                contract_id = res.get('contract_id')
                input_lines = list(other_inputs)
                for line in input_lines:
                    line[2].update({'contract_id':contract_id})
                #input_lines = map(lambda x: x[2].update({'contract_id':contract_id}),input_lines)
                res.update({'input_line_ids': input_lines,})
            res.update({'dias_pagar': payslip_batch.dias_pagar,
                            'imss_dias': payslip_batch.imss_dias,
                            'imss_mes': payslip_batch.imss_mes,
                            'ultima_nomina': payslip_batch.ultima_nomina,
                            'mes': '{:02d}'.format(to_date.month),
                            'isr_devolver': payslip_batch.isr_devolver,
                            'isr_ajustar': payslip_batch.isr_ajustar,
                            'isr_anual': payslip_batch.isr_anual,
                            'periodicidad_pago': payslip_batch.periodicidad_pago,
                            'no_periodo': payslip_batch.no_periodo,
                            'concepto_periodico': payslip_batch.concepto_periodico})

            payslips += self.env['hr.payslip'].create(res)
            
        payslips.compute_sheet()
        
        return {'type': 'ir.actions.act_window_close'}