# -*- coding: utf-8 -*-

import base64
import xlrd
from odoo.exceptions import ValidationError
from odoo import api, fields, models


class ImportarMovimientosFaltas(models.TransientModel):
    _name = 'importar.movimientos.retardos'

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

            datos = {
                'fecha': fch_inicio,
                'employee_id': employee_id.id,
            }

            consolidado_lineas.append(datos)

        for retardo_nomina in consolidado_lineas:
            retardo_nomina_id = self.env['retardo.nomina'].create(retardo_nomina)
            retardo_nomina_id.action_validar()

        return {'type': 'ir.actions.client', 'tag': 'reload'}

