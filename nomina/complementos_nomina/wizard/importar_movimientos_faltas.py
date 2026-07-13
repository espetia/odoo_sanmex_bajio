# -*- coding: utf-8 -*-

import base64
import xlrd
from odoo.exceptions import ValidationError
from odoo import api, fields, models

TIPO_FALTAS = ('Justificada con goce de sueldo', 'Justificada sin goce de sueldo', 'Injustificada', 'Por retardos')


class ImportarMovimientosFaltas(models.TransientModel):
    _name = 'importar.movimientos.faltas'

    archivo = fields.Binary(string='Archivo (*.xlsx)', required=True)

    def importar_archivo(self):
        decoded_data = base64.decodebytes(self.archivo)
        wb = xlrd.open_workbook(file_contents=decoded_data)
        worksheet = wb.sheet_by_index(0)

        consolidado_lineas = []
        for fila in range(1, worksheet.nrows):
            no_empleado = worksheet.cell(fila, 0).value
            departmento = worksheet.cell(fila, 1).value
            compania = worksheet.cell(fila, 2).value
            fch_inicio = worksheet.cell(fila, 3).value
            fch_fin = worksheet.cell(fila, 4).value
            tipo_falta = worksheet.cell(fila, 5).value
            if not no_empleado:
                msg = 'Error en la la línea {0}:\n' \
                      'No contiene número del empleado'.format(fila + 1)
                raise ValidationError(msg)
            no_empleado = int(no_empleado)
            if not departmento:
                msg = 'Error en la la línea {0}:\n' \
                      'no contiene departmento'.format(fila + 1)
                raise ValidationError(msg)
            if not compania:
                msg = u'Error en la la línea {0}:\n' \
                      u'no contiene compañía'.format(fila + 1)
                raise ValidationError(msg)
            if not fch_inicio:
                msg = 'Error en la la línea {0}:\n' \
                      'no contiene fecha de inicio'.format(fila + 1)
                raise ValidationError(msg)
            fch_inicio = xlrd.xldate.xldate_as_datetime(fch_inicio, wb.datemode).date()
            if not fch_fin:
                msg = 'Error en la la línea {0}:\n' \
                      'no contiene fecha de fin'.format(fila + 1)
                raise ValidationError(msg)
            fch_fin = xlrd.xldate.xldate_as_datetime(fch_fin, wb.datemode).date()
            if not tipo_falta:
                msg = 'Error en la la línea {0}:\n' \
                      'no contiene tipo de falta'.format(fila + 1)
                raise ValidationError(msg)
            company_id = self.env['res.company'].search([('name', '=', compania)])
            if not company_id:
                msg = 'Error en la la línea {0}:\n' \
                      'No se ha encontrado la compañía: {1}'.format(fila + 1, compania)
                raise ValidationError(msg)
            department_id = self.env['hr.department'].search([
                ('name', '=', departmento),
                ('company_id', '=', company_id.id),
            ])
            if not department_id:
                msg = 'Error en la la línea {0}:\n' \
                      'No se ha encontrado el departamento: {1}, para la compañía: {2}'.format(fila + 1, departmento, compania)
                raise ValidationError(msg)
            employee_id = self.env['hr.employee'].search([
                ('no_empleado', '=', no_empleado),
                ('department_id', '=', department_id.id),
                ('company_id', '=', company_id.id),
            ])
            if not employee_id:
                msg = 'Error en la la línea {0}:\n' \
                      'No se ha encontrado el número de empleado: {1}, en el departamento: {2}, ' \
                      'para la compañía: {3}'.format(fila + 1, no_empleado, departmento, compania)
                raise ValidationError(msg)
            if tipo_falta not in TIPO_FALTAS:
                msg = 'Error en la la línea {0}:\n' \
                      'El tipo de falta: {1}, no es un tipo de falta válido.\n' \
                      'Los tipos de falta válidos son: Justificada con goce de sueldo, Justificada sin goce de sueldo, Injustificada, Por retardos'.format(fila + 1, tipo_falta)
                raise ValidationError(msg)
            if tipo_falta == 'Por retardos':
                tipo_falta = 'retardo'
            if fch_inicio > fch_fin:
                msg = 'Error en la la línea {0}:\n' \
                      'La fecha de inicio no puede ser mayor que la fecha de fin.'.format(fila + 1)
                raise ValidationError(msg)

            dias = 0
            diferencia = str(fch_fin - fch_inicio)
            if 'day' in diferencia or 'days' in diferencia:
                dias = int(diferencia.split(' ')[0])

            datos = {
                'fecha_inicio': fch_inicio,
                'fecha_fin': fch_fin,
                'tipo_de_falta': tipo_falta,
                'dias': dias + 1,
                'employee_id': employee_id.id,
            }

            consolidado_lineas.append(datos)

        for falta in consolidado_lineas:
            falta_id = self.env['faltas.nomina'].create(falta)
            falta_id.action_validar()

        return {'type': 'ir.actions.client', 'tag': 'reload'}

