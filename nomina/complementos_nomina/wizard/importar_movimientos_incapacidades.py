# -*- coding: utf-8 -*-

import base64
import xlrd
from odoo.exceptions import ValidationError
from odoo import api, fields, models

RAMO_DE_SEGURO = ('Riesgo de trabajo', 'Enfermedad general', 'Maternidad')
CONTROL = ('Unica', 'Inicial', 'Subsecuente', 'Alta médica o ST-2')
CONTROL2 = ('Prenatal o ST-3', 'Enalce', 'Postnatal')


class ImportarMovimientosFaltas(models.TransientModel):
    _name = 'importar.movimientos.incapacidades'

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
            ramo = worksheet.cell(fila, 3).value
            fch_inicio = worksheet.cell(fila, 4).value
            dias = worksheet.cell(fila, 5).value
            control = worksheet.cell(fila, 6).value
            folio = worksheet.cell(fila, 7).value
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
            if not ramo:
                msg = u'Error en la la línea {0}:\n' \
                      u'no contiene ramo de seguro'.format(fila + 1)
                raise ValidationError(msg)
            if ramo not in RAMO_DE_SEGURO:
                msg = 'Error en la la línea {0}:\n' \
                      'El ramo de seguro: {1}, no es válido.\n' \
                      'Los ramo de seguro válidos son: Riesgo de trabajo, Enfermedad general, Maternidad'.format(fila + 1, ramo)
                raise ValidationError(msg)
            if not fch_inicio:
                msg = 'Error en la la línea {0}:\n' \
                      'no contiene fecha de inicio'.format(fila + 1)
                raise ValidationError(msg)
            fch_inicio = xlrd.xldate.xldate_as_datetime(fch_inicio, wb.datemode).date()
            if not dias:
                msg = u'Error en la la línea {0}:\n' \
                      u'no contiene dias'.format(fila + 1)
                raise ValidationError(msg)
            if not int(dias) > 0:
                msg = 'Error en la la línea {0}:\n' \
                      'La cantidad de dias debe ser mayor a 0'.format(fila + 1, )
                raise ValidationError(msg)
            if not control:
                msg = u'Error en la la línea {0}:\n' \
                      u'no contiene control'.format(fila + 1)
                raise ValidationError(msg)
            if control not in CONTROL and control not in CONTROL2:
                msg = 'Error en la la línea {0}:\n' \
                      'El control: {1}, no es válido.\n' \
                      'Los controles válidos son: Unica, Inicial, Subsecuente, Alta médica o ST-2, Prenatal o ST-3, Enalce, Postnatal'.format(fila + 1, control)
                raise ValidationError(msg)
            if control in CONTROL2:
                if control == 'Prenatal o ST-3':
                    control_final = '01'
                elif control == 'Enalce':
                    control_final = '02'
                elif control == 'Postnatal':
                    control_final = '03'
            if not folio:
                msg = u'Error en la la línea {0}:\n' \
                      u'no contiene folio'.format(fila + 1)
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

            datos = {
                'employee_id': employee_id.id,
                'ramo_de_seguro': ramo,
                'fecha': fch_inicio,
                'dias': int(dias),
                'folio_incapacidad': folio,
            }

            if control in CONTROL:
                datos['control'] = control
            else:
                datos['control2'] = control_final

            consolidado_lineas.append(datos)

        for incapacidad_nomina in consolidado_lineas:
            incapacidad_nomina_id = self.env['incapacidades.nomina'].create(incapacidad_nomina)
            incapacidad_nomina_id.action_validar()

        return {'type': 'ir.actions.client', 'tag': 'reload'}

