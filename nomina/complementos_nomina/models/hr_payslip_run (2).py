# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

import pytz
from datetime import date
from datetime import datetime
import xlwt
import io
from xlwt import easyxf
from odoo.exceptions import UserError
from odoo import models, fields, api, _
import base64
from decimal import Decimal

class HrPayslipRun(models.Model):
    _inherit = 'hr.payslip.run'

    first_payslip_month = fields.Boolean(string="First payslip of month")
    pay_pantry_vouchers = fields.Boolean(string="Pay pantry vouchers")
    state = fields.Selection([
        ('draft', 'Draft'),
        ('done', 'Done'),
        ('close', 'Close'),
    ], string='Status', index=True, readonly=True, copy=False, default='draft')
    company_id = fields.Many2one(
        comodel_name='res.company',
        string='Compañía',
        default=lambda self: self.env.company
    )
    filecontent = fields.Binary(string='Archivo')
    Fecha_TXT = datetime.now(pytz.timezone('America/Mexico_City')).strftime('%Y-%m-%d %H:%M:%S')

    def generate_file(self):
        #txt_total = fields.One2many('hr.payslip', 'employee_id', string='Payslips', readonly=True)
        #txt_total = 'HOLA MUNDO \r\nHOLA MUNDO'
        v_contador = 1
        txt_total = ''

        newslip_ids = sorted(self.slip_ids, key=lambda num : num.employee_id.no_empleado)
        for record in newslip_ids:
            no_cuenta = record.employee_id.no_cuenta
            empleado = record.employee_id.name

            re_empleado = str(empleado).replace('Ñ', 'N')

            r_Total_Salario = ''
            #print("Texto Extraido", record.name)
            for record2 in record.line_ids:
                if record2.code == 'EFECT':
                    total_salario = record2.total
                    d_total_salario = Decimal(total_salario)
                    q_decimal_Total_Salario = round(d_total_salario, 2)
                    v_Total_Salario = str(q_decimal_Total_Salario).split('.')
                    #print("Texto Extraido", record2.amount)
                    r_Total_Salario = v_Total_Salario[0] + v_Total_Salario[1]

            if no_cuenta is False:
                errorData = ("Se elimino un dato del .txt de la persona" + " " + re_empleado + " " + "Porque no tiene número de cuenta...")
                print(errorData)
            else:
                txt_total += str(v_contador).rjust(9, '0') + '                ' + '99' + str(no_cuenta) + '          ' + str(r_Total_Salario).rjust(15, '0') + (re_empleado).ljust(39, ' ') + ' ' + '001001\r\n'
                v_contador += 1


        output = io.BytesIO(io.StringIO(txt_total).read().encode('utf8'))
        self.filecontent = base64.b64encode(output.read())
        filename_field = ('Nomina_Empleados_{0}'.format(self.Fecha_TXT))
        if self.filecontent:
            return {
                'res_model': 'ir.actions.act_url',
                'type': 'ir.actions.act_url',
                'target': 'new',
                'url': (
                    'web/content/?model=hr.payslip.run&id={0}'
                    '&filename_field={1}'
                    '&field=filecontent&download=true'
                    '&filename={1}.txt'.format(
                        self.id,
                        filename_field,
                    )
                )
            }
    
    def confirmar_todas(self):
        for slip_id in self.slip_ids:
            if slip_id.state == 'draft':
                slip_id.action_payslip_done()
        self.state = 'done'

    def reversar_todas(self):
        for slip_id in self.slip_ids:
            if slip_id.state == 'done':
                slip_id.action_payslip_cancel()
                slip_id.action_payslip_draft()
        self.state = 'draft'

    def timbrar_nomina(self):
        self.ensure_one()
        #cr = self._cr
        payslip_obj = self.env['hr.payslip']
        for payslip_id in self.slip_ids.ids:
            payslip = payslip_obj.browse(payslip_id)
            # if payslip.state in ['draft','verify']:
            if payslip.state in ['verify','done'] and payslip.estado_factura == 'factura_no_generada':
               payslip.action_payslip_done()
               try:
                   if not payslip.nomina_cfdi:
                      payslip.action_cfdi_nomina_generate()
               except Exception as e:
                   pass
        return

    @api.onchange('pay_pantry_vouchers')
    def _onchange_pantry_vouchers(self):
        for line in self.slip_ids:
            if self.pay_pantry_vouchers:
                line.pay_pantry_vouchers = True
            else:
                line.pay_pantry_vouchers = False

    def get_department(self):
        result = {}
        department = self.env['hr.department'].search([])
        for dept in department:
            result[dept.id] = dept.name
        return result

    def get_dept_total(self, dept_id):
        result = {}
        for rule in self.env['hr.salary.rule'].search([]):
            result[rule.code] = 0
        for payslip in self.slip_ids:
            if payslip.employee_id.department_id.id == dept_id and payslip.state != "cancel":
                for line in payslip.line_ids:
                    if line.code in result.keys():
                        result[line.code] = round(line.total + result.get(line.code), 2)
                    else:
                        result[line.code] = round(line.total, 2)
        return result

    def get_grand_total(self):
        result = {}
        for rule in self.env['hr.salary.rule'].search([]):
            result[rule.code] = 0
        for payslip in self.slip_ids:
            if payslip.state != "cancel":
                for line in payslip.line_ids:
                    if line.code in result.keys():
                        result[line.code] = round(line.total + result.get(line.code), 2)
                    else:
                        result[line.code] = round(line.total, 2)
        return result

    def get_payslip_group_by_department(self):
        result = {}
        for line in self.slip_ids:
            if line.employee_id.department_id.id in result.keys():
                result[line.employee_id.department_id.id].append(line)
            else:
                result[line.employee_id.department_id.id] = [line]
        return result

    def get_payslip_group_by_payslip_number(self):
        result = {}
        for line in self.slip_ids:
            if line.employee_id.id in result.keys():
                result[line.employee_id.id].append(line)
            else:
                result[line.employee_id.id] = [line]
        return result

    def get_all_columns(self):
        result = {}
        all_col_list_seq = []
        if self.slip_ids:
            for line in self.env['hr.payslip.line'].search([('slip_id', 'in', self.slip_ids.ids)], order="sequence"):
                if line.code not in all_col_list_seq:
                    all_col_list_seq.append(line.code)
                if line.code not in result.keys():
                    result[line.code] = line.name
        #         for payslip in self.slip_ids:
        #             for line in payslip.line_ids:
        #                 if line.code not in result.keys():
        #                     result[line.code] = line.name
        return [result, all_col_list_seq]

    def export_report_xlsx_1(self):
        import base64
        workbook = xlwt.Workbook()
        worksheet = workbook.add_sheet('Listado de nómina')

        text_bold_left_title = easyxf('font:height 300; align: horiz center; font:bold True;')
        text_bold_left_subtitle = easyxf('font:height 250; align: horiz center;')
        text_bold_left_paragrah = easyxf('font:height 160; align: horiz left;')
        text_bold_center_paragrah = easyxf('font:height 160; align: horiz center;')

        tz_mx = pytz.timezone('America/Mexico_City')
        now = datetime.now(tz_mx)
        today = date.today()

        money_format = xlwt.XFStyle()
        money_format.num_format_str = '#,##0.00'
        money_format.font.height = 180
        money_format.alignment.HORZ_RIGHT = True

        money_format_b = xlwt.XFStyle()
        money_format_b.num_format_str = '#,##0.00'
        money_format_b.font.height = 180
        money_format_b.font.bold = True
        money_format_b.alignment.HORZ_RIGHT = True

        money_format_n = xlwt.XFStyle()
        money_format_n.num_format_str = '#,##0.00'
        money_format_n.font.height = 180
        money_format_n.alignment.HORZ_RIGHT = True

        font_format = xlwt.XFStyle()
        font_format.font.height = 180
        font_format.alignment.HORZ_LEFT = True

        font_format_r = xlwt.XFStyle()
        font_format_r.font.height = 180
        font_format_r.alignment.HORZ_RIGHT = True

        font_format_r_b = xlwt.XFStyle()
        font_format_r_b.font.height = 180
        font_format_r_b.font.bold = True
        font_format_r_b.alignment.HORZ_RIGHT = True

        font_format_l_b = xlwt.XFStyle()
        font_format_l_b.font.height = 180
        font_format_l_b.font.bold = True
        font_format_l_b.alignment.HORZ_LEFT = True

        font_format_h = xlwt.XFStyle()
        font_format_h.font.height = 200
        font_format_h.font.bold = True
        font_format_h.alignment.wrap = True
        font_format_h.alignment.HORZ_CENTER = True

        pattern = xlwt.Pattern()
        pattern.pattern = xlwt.Pattern.SOLID_PATTERN
        pattern.pattern_fore_colour = xlwt.Style.colour_map['lavender']
        font_format_h.pattern = pattern

        border = xlwt.Borders()
        border.left = 1
        border.right = 1
        border.top = 2
        border.bottom = 2
        border.right_colour = xlwt.Style.colour_map['plum']
        border.left_colour = xlwt.Style.colour_map['plum']
        border.top_colour = xlwt.Style.colour_map['plum']
        border.bottom_colour = xlwt.Style.colour_map['plum']
        font_format_h.borders = border

        worksheet.write(3, 0, 'Código', font_format_h)
        worksheet.write(3, 1, 'Empleado', font_format_h)
        worksheet.write(3, 2, 'Dias Pag', font_format_h)
        worksheet.write(3, 3, 'SD', font_format_h)
        worksheet.write(3, 4, 'SDI', font_format_h)
        worksheet.write(3, 5, 'SBC', font_format_h)
        # inicio cambios
        # leave_ids = self.env['hr.leave.type'].search([])
        # contador = 0
        # leave_types = {}
        # for leave_id in leave_ids:
        #    worksheet.write(0, 6 + contador, leave_id.name, header_style)
        #    leave_types[leave_id.name] = 6 + contador
        #    contador += 1
        # col_nm = 6 + contador
        # fin cambios
        col_nm = 6
        all_column = self.get_all_columns()
        # print("All_columns", all_column)
        all_col_dict = all_column[0]
        all_col_list = all_column[1]
        # print("All_col_dict", all_col_dict)
        # print("All_col_list", all_col_list)
        for col in all_col_list:
            cadena = all_col_dict[col].upper()
            find_exent = cadena.find("EXENTO")
            find_exent_1 = cadena.find("EXENTA")
            find_gravado = cadena.find("GRAVADO")
            find_gravado_1 = cadena.find("GRAVADA")
            if find_exent == -1 and find_exent_1 == -1 and find_gravado == -1 and find_gravado_1 == -1:
                # print("name right:", all_col_dict[col])
                worksheet.write(3, col_nm, all_col_dict[col], font_format_h)
                col_nm += 1
        for t in ['Total Efectivo', 'Total Especie']:
            # print("monto", t)
            worksheet.write(3, col_nm, t, font_format_h)
            col_nm += 1

        payslip_group_by_payslip_number = self.get_payslip_group_by_payslip_number()
        row = 4
        grand_total = {}
        company_name = self.company_id.name
        for dept in self.env['hr.employee'].browse(payslip_group_by_payslip_number.keys()).sorted(lambda x: x.no_empleado):
            #company_name = self.company_id.name
            # row += 1
            # worksheet.write_merge(row, row, 0, 5, dept.name, text_bold_left)
            total = {}
            # row += 1
            slip_sorted_by_employee = {}
            hr_payslips = []
            for slip in payslip_group_by_payslip_number[dept.id]:
                if slip.employee_id:
                    slip_sorted_by_employee[slip.id] = slip.employee_id.no_empleado or '0'
            for values in sorted(slip_sorted_by_employee.values()):
                val_list = list(slip_sorted_by_employee.values())
                key_list = list(slip_sorted_by_employee.keys())
                # print("key list", slip_sorted_by_employee.keys())
                slip = key_list[val_list.index(values)]
                # print("value slip", slip)
                hr_payslips.append(self.env['hr.payslip'].browse(slip))
            # inicio cambios
            x = {}
            for num, record in enumerate(hr_payslips):
                x[str(num)] = record.employee_id.name
            ordenado = {k: v for k, v in sorted(x.items(), key=lambda item: item[1])}
            x = []
            for record in ordenado.keys():
                x.append(hr_payslips[int(record)])
            hr_payslips = x
            # fin cambios
            for slip in hr_payslips:
                if slip.state == "cancel":
                    continue
                if slip.employee_id.no_empleado:
                    worksheet.write(row, 0, slip.employee_id.no_empleado, font_format)
                worksheet.write(row, 1, slip.employee_id.name, font_format)
                work_day = slip.get_total_work_days()
                worksheet.write(row, 2, work_day, money_format_n)
                worksheet.write(row, 3, slip.employee_id.contract_id.sueldo_diario, money_format)
                worksheet.write(row, 4, slip.employee_id.contract_id.sueldo_diario_integrado, money_format)
                worksheet.write(row, 5, slip.employee_id.contract_id.sueldo_base_cotizacion, money_format)
                # code_col = 6 + contador
                code_col = 6
                # inicio cambios
                # coincidencias = []
                # for line in slip.worked_days_line_ids:
                #    if line.code in leave_types:
                #        worksheet.write(row, leave_types[line.code], line.number_of_days, text_right)
                #        coincidencias.append(line.code)
                # pendientes = list(leave_types.keys() - coincidencias)
                # for pendiente in pendientes:
                #    worksheet.write(row, leave_types[pendiente], 0, text_right)
                # fin cambios
                for code in all_col_list:
                    # print("Name col", all_col_dict[code])
                    # print("codigo_f1", code)
                    cadena = all_col_dict[code].upper()
                    find_exent = cadena.find("EXENTO")
                    find_exent_1 = cadena.find("EXENTA")
                    find_gravado = cadena.find("GRAVADO")
                    find_gravado_1 = cadena.find("GRAVADA")
                    if find_exent == -1 and find_exent_1 == -1 and find_gravado == -1 and find_gravado_1 == -1:
                        amt = 0
                        if code in total.keys():
                            amt = slip.get_amount_from_rule_code(code)
                            if amt:
                                grand_total[code] = grand_total.get(code) + amt
                                total[code] = total.get(code) + amt
                        else:
                            amt = slip.get_amount_from_rule_code(code)
                            total[code] = amt or 0
                            if code in grand_total.keys():
                                grand_total[code] = amt + grand_total.get(code) or 0.0
                            else:
                                grand_total[code] = amt or 0
                        worksheet.write(row, code_col, round(amt, 2), money_format)
                        code_col += 1
                worksheet.write(row, code_col, round(slip.get_total_code_value('001'), 2), money_format)
                code_col += 1
                worksheet.write(row, code_col, round(slip.get_total_code_value('002'), 2), money_format)
                row += 1
            # worksheet.write_merge(row, row, 0, 5, 'Total Departamento', text_bold_left)
            # code_col = 6 + contador
            # code_col = 6
            # for code in all_col_list:
            #    cadena = all_col_dict[code].upper()
            #    find_exent = cadena.find("EXENTO")
            #    find_exent_1 = cadena.find("EXENTA")
            #    find_gravado = cadena.find("GRAVADO")
            #    find_gravado_1 = cadena.find("GRAVADA")
            #    if find_exent == -1 and find_exent_1 == -1 and find_gravado == -1 and find_gravado_1 == -1:
            #        worksheet.write(row, code_col, total.get(code), text_bold_right)
            #        code_col += 1
        row += 1
        worksheet.write_merge(row, row, 0, 5, 'Gran Total', font_format_l_b)
        # code_col = 6 + contador
        code_col = 6
        for code in all_col_list:
            cadena = all_col_dict[code].upper()
            find_exent = cadena.find("EXENTO")
            find_exent_1 = cadena.find("EXENTA")
            find_gravado = cadena.find("GRAVADO")
            find_gravado_1 = cadena.find("GRAVADA")
            if find_exent == -1 and find_exent_1 == -1 and find_gravado == -1 and find_gravado_1 == -1:
                worksheet.write(row, code_col, round(grand_total.get(code), 2), money_format_b)
                code_col += 1
            name_payslip = self.name

        name_payslip = self.name
        period = 'Periodo del ' + self.date_start.strftime('%d/%m/%Y') + ' al ' + self.date_end.strftime('%d/%m/%Y')
        worksheet.write_merge(0, 0, 1, 4, company_name, text_bold_left_title)
        worksheet.write_merge(1, 1, 1, 4, name_payslip, text_bold_left_subtitle)
        worksheet.write_merge(1, 1, 5, 6, 'Hora :' + now.strftime("%H:%M:%S"), text_bold_left_paragrah)
        worksheet.write_merge(2, 2, 1, 4, period, text_bold_center_paragrah)
        worksheet.write_merge(2, 2, 5, 6, 'Fecha :' + today.strftime("%d/%m/%Y"), text_bold_left_paragrah)

        #
        #Hoja 2
        #
        worksheet = workbook.add_sheet('Listado de nómina por departamento')
        worksheet.write(3, 0, 'Cod', font_format_h)
        worksheet.write(3, 1, 'Empleado', font_format_h)
        worksheet.write(3, 2, 'Dias Pag', font_format_h)
        worksheet.write(3, 3, 'SD', font_format_h)
        worksheet.write(3, 4, 'SDI', font_format_h)
        worksheet.write(3, 5, 'SBC', font_format_h)
        # inicio cambios
        #leave_ids = self.env['hr.leave.type'].search([])
        #contador = 0
        #leave_types = {}
        #for leave_id in leave_ids:
        #    worksheet.write(0, 6 + contador, leave_id.name, header_style)
        #    leave_types[leave_id.name] = 6 + contador
        #    contador += 1
        #col_nm = 6 + contador
        # fin cambios
        col_nm = 6
        all_column = self.get_all_columns()
        #print("All_columns", all_column)
        all_col_dict = all_column[0]
        all_col_list = all_column[1]
        #print("All_col_dict", all_col_dict)
        #print("All_col_list", all_col_list)
        for col in all_col_list:
            cadena = all_col_dict[col].upper()
            find_exent = cadena.find("EXENTO")
            find_exent_1 = cadena.find("EXENTA")
            find_gravado = cadena.find("GRAVADO")
            find_gravado_1 = cadena.find("GRAVADA")
            if find_exent == -1 and find_exent_1 == -1 and find_gravado == -1 and find_gravado_1 == -1:
                #print("name right:", all_col_dict[col])
                worksheet.write(3, col_nm, all_col_dict[col], font_format_h)
                col_nm += 1
        for t in ['Total Efectivo', 'Total Especie']:
            #print("monto", t)
            worksheet.write(3, col_nm, t, font_format_h)
            col_nm += 1

        payslip_group_by_department = self.get_payslip_group_by_department()
        row = 4
        grand_total = {}
        company_name = self.company_id.name
        for dept in self.env['hr.department'].browse(payslip_group_by_department.keys()).sorted(lambda x: x.name):
            #company_name = self.company_id.name
            row += 1
            worksheet.write_merge(row, row, 0, 5, dept.name, font_format_l_b)
            total = {}
            row += 1
            slip_sorted_by_employee = {}
            hr_payslips = []
            for slip in payslip_group_by_department[dept.id]:
                if slip.employee_id:
                    slip_sorted_by_employee[slip.id] = slip.employee_id.no_empleado or '0'
            for values in sorted(slip_sorted_by_employee.values()):
                val_list = list(slip_sorted_by_employee.values())
                key_list = list(slip_sorted_by_employee.keys())
                #print("key list", slip_sorted_by_employee.keys())
                slip = key_list[val_list.index(values)]
                #print("value slip", slip)
                hr_payslips.append(self.env['hr.payslip'].browse(slip))
            # inicio cambios
            x = {}
            for num, record in enumerate(hr_payslips):
                x[str(num)] = record.employee_id.name
            ordenado = {k: v for k, v in sorted(x.items(), key=lambda item: item[1])}
            x = []
            for record in ordenado.keys():
                x.append(hr_payslips[int(record)])
            hr_payslips = x
            # fin cambios
            for slip in hr_payslips:
                if slip.state == "cancel":
                    continue
                if slip.employee_id.no_empleado:
                    worksheet.write(row, 0, slip.employee_id.no_empleado, font_format)
                worksheet.write(row, 1, slip.employee_id.name, font_format)
                work_day = slip.get_total_work_days()
                worksheet.write(row, 2, work_day, money_format_n)
                worksheet.write(row, 3, slip.employee_id.contract_id.sueldo_diario, money_format)
                worksheet.write(row, 4, slip.employee_id.contract_id.sueldo_diario_integrado, money_format)
                worksheet.write(row, 5, slip.employee_id.contract_id.sueldo_base_cotizacion, money_format)
                #code_col = 6 + contador
                code_col = 6
                # inicio cambios
                #coincidencias = []
                #for line in slip.worked_days_line_ids:
                #    if line.code in leave_types:
                #        worksheet.write(row, leave_types[line.code], line.number_of_days, text_right)
                #        coincidencias.append(line.code)
                #pendientes = list(leave_types.keys() - coincidencias)
                #for pendiente in pendientes:
                #    worksheet.write(row, leave_types[pendiente], 0, text_right)
                # fin cambios
                for code in all_col_list:
                    #print("Name col", all_col_dict[code])
                    #print("codigo_f1", code)
                    cadena = all_col_dict[code].upper()
                    find_exent = cadena.find("EXENTO")
                    find_exent_1 = cadena.find("EXENTA")
                    find_gravado = cadena.find("GRAVADO")
                    find_gravado_1 = cadena.find("GRAVADA")
                    if find_exent == -1 and find_exent_1 == -1 and find_gravado == -1 and find_gravado_1 == -1:
                        amt = 0
                        if code in total.keys():
                            amt = slip.get_amount_from_rule_code(code)
                            if amt:
                                grand_total[code] = grand_total.get(code) + amt
                                total[code] = total.get(code) + amt
                        else:
                            amt = slip.get_amount_from_rule_code(code)
                            total[code] = amt or 0
                            if code in grand_total.keys():
                                grand_total[code] = amt + grand_total.get(code) or 0.0
                            else:
                                grand_total[code] = amt or 0
                        worksheet.write(row, code_col, amt, money_format)
                        code_col += 1
                worksheet.write(row, code_col, slip.get_total_code_value('001'), money_format)
                code_col += 1
                worksheet.write(row, code_col, slip.get_total_code_value('002'), money_format)
                row += 1
            worksheet.write_merge(row, row, 0, 5, 'Total Departamento', font_format_l_b)
            #code_col = 6 + contador
            code_col = 6
            for code in all_col_list:
                cadena = all_col_dict[code].upper()
                find_exent = cadena.find("EXENTO")
                find_exent_1 = cadena.find("EXENTA")
                find_gravado = cadena.find("GRAVADO")
                find_gravado_1 = cadena.find("GRAVADA")
                if find_exent == -1 and find_exent_1 == -1 and find_gravado == -1 and find_gravado_1 == -1:
                    worksheet.write(row, code_col, total.get(code), money_format_b)
                    code_col += 1
        row += 1
        worksheet.write_merge(row, row, 0, 5, 'Gran Total', font_format_l_b)
        #code_col = 6 + contador
        code_col = 6
        for code in all_col_list:
            cadena = all_col_dict[code].upper()
            find_exent = cadena.find("EXENTO")
            find_exent_1 = cadena.find("EXENTA")
            find_gravado = cadena.find("GRAVADO")
            find_gravado_1 = cadena.find("GRAVADA")
            if find_exent == -1 and find_exent_1 == -1 and find_gravado == -1 and find_gravado_1 == -1:
                worksheet.write(row, code_col, grand_total.get(code), money_format_b)
                code_col += 1

        name_payslip = self.name
        period = 'Periodo del ' + self.date_start.strftime('%d/%m/%Y') + ' al ' + self.date_end.strftime('%d/%m/%Y')
        worksheet.write_merge(0, 0, 1, 4, company_name, text_bold_left_title)
        worksheet.write_merge(1, 1, 1, 4, name_payslip, text_bold_left_subtitle)
        worksheet.write_merge(1, 1, 5, 6, 'Hora :' + now.strftime("%H:%M:%S"), text_bold_left_paragrah)
        worksheet.write_merge(2, 2, 1, 4, period, text_bold_center_paragrah)
        worksheet.write_merge(2, 2, 5, 6, 'Fecha :' + today.strftime("%d/%m/%Y"), text_bold_left_paragrah)

        fp = io.BytesIO()
        workbook.save(fp)
        fp.seek(0)
        data = fp.read()
        fp.close()
        self.write({'file_data': base64.b64encode(data)})
        action = {
            'name': 'Journal Entries',
            'type': 'ir.actions.act_url',
            'url': "/web/content/?model=hr.payslip.run&id=" + str(
                self.id) + "&field=file_data&download=true&filename=Listado_de_nomina.xls",
            'target': 'self',
        }
        return action


    def export_report_xlsx(self):
        import base64
        workbook = xlwt.Workbook()
        worksheet = workbook.add_sheet('Listado de nomina')
        header_style = easyxf('font:height 200; align: horiz center; font:bold True;' "borders: top thin,left thin,right thin,bottom thin")
        text_bold_left = easyxf('font:height 200; font:bold True; align: horiz left;' "borders: top thin,bottom thin")
        text_left = easyxf('font:height 200; align: horiz left;' "borders: top thin,bottom thin")
        text_right = easyxf('font:height 200; align: horiz right;' "borders: top thin,bottom thin")
        text_bold_right = easyxf('font:height 200;font:bold True; align: horiz right;' "borders: top thin,bottom thin")
        worksheet.write(0, 0, 'Cod', header_style)
        worksheet.write(0, 1, 'Empleado', header_style)
        worksheet.write(0, 2, 'Dias Pag', header_style)
        worksheet.write(0, 3, 'SD', header_style)
        worksheet.write(0, 4, 'SDI', header_style)
        worksheet.write(0, 5, 'SBC', header_style)
        # inicio cambios
        leave_ids = self.env['hr.leave.type'].search([])
        contador = 0
        leave_types = {}
        for leave_id in leave_ids:
            worksheet.write(0, 6 + contador, leave_id.name, header_style)
            leave_types[leave_id.name] = 6 + contador
            contador += 1
        # fin cambios
        col_nm = 6 + contador
        all_column = self.get_all_columns()
        all_col_dict = all_column[0]
        all_col_list = all_column[1]
        for col in all_col_list:
            worksheet.write(0, col_nm, all_col_dict[col], header_style)
            col_nm += 1
        for t in ['Total Efectivo', 'Total Especie']:
            worksheet.write(0, col_nm, t, header_style)
            col_nm += 1
        
        payslip_group_by_department = self.get_payslip_group_by_department()
        row = 1
        grand_total = {}
        for dept in self.env['hr.department'].browse(payslip_group_by_department.keys()).sorted(lambda x: x.name):
            row += 1
            worksheet.write_merge(row, row, 0, 5, dept.name, text_bold_left)
            total = {}
            row += 1
            slip_sorted_by_employee = {}
            hr_payslips = []
            for slip in payslip_group_by_department[dept.id]:
                if slip.employee_id:
                    slip_sorted_by_employee[slip.id] = slip.employee_id.no_empleado or '0'
            for values in sorted(slip_sorted_by_employee.values()):
                val_list = list(slip_sorted_by_employee.values())
                key_list = list(slip_sorted_by_employee.keys())
                slip = key_list[val_list.index(values)]  
                hr_payslips.append(self.env['hr.payslip'].browse(slip))
            # inicio cambios
            x = {}
            for num, record in enumerate(hr_payslips):
                x[str(num)] = record.employee_id.name
            ordenado = {k: v for k, v in sorted(x.items(), key=lambda item: item[1])}
            x = []
            for record in ordenado.keys():
                x.append(hr_payslips[int(record)])
            hr_payslips = x
            # fin cambios
            for slip in hr_payslips:
                if slip.state == "cancel":
                    continue
                if slip.employee_id.no_empleado:
                    worksheet.write(row, 0, slip.employee_id.no_empleado, text_left)
                worksheet.write(row, 1, slip.employee_id.name, text_left)
                work_day = slip.get_total_work_days()
                worksheet.write(row, 2, work_day, text_right)
                worksheet.write(row, 3, slip.employee_id.contract_id.sueldo_diario, text_right)
                worksheet.write(row, 4, slip.employee_id.contract_id.sueldo_diario_integrado, text_right)
                worksheet.write(row, 5, slip.employee_id.contract_id.sueldo_base_cotizacion, text_right)
                code_col = 6 + contador
                # inicio cambios
                coincidencias = []
                for line in slip.worked_days_line_ids:
                    if line.code in leave_types:
                        worksheet.write(row, leave_types[line.code], line.number_of_days, text_right)
                        coincidencias.append(line.code)
                pendientes = list(leave_types.keys() - coincidencias)
                for pendiente in pendientes:
                    worksheet.write(row, leave_types[pendiente], 0, text_right)
                # fin cambios
                for code in all_col_list:
                    amt = 0
                    if code in total.keys():
                        amt = slip.get_amount_from_rule_code(code)
                        if amt:
                            grand_total[code] = grand_total.get(code) + amt
                            total[code] = total.get(code) + amt
                    else:
                        amt = slip.get_amount_from_rule_code(code)
                        total[code] = amt or 0
                        if code in grand_total.keys():
                            grand_total[code] = amt + grand_total.get(code) or 0.0
                        else:
                            grand_total[code] = amt or 0
                    worksheet.write(row, code_col, amt, text_right)
                    code_col += 1
                worksheet.write(row, code_col, slip.get_total_code_value('001'), text_right)
                code_col += 1
                worksheet.write(row, code_col, slip.get_total_code_value('002'), text_right)
                row += 1
            worksheet.write_merge(row, row, 0, 5, 'Total Departamento', text_bold_left)
            code_col = 6 + contador
            for code in all_col_list:
                worksheet.write(row, code_col, total.get(code), text_bold_right)
                code_col += 1
        row += 1
        worksheet.write_merge(row, row, 0, 5, 'Gran Total', text_bold_left)
        code_col = 6 + contador
        for code in all_col_list:
            worksheet.write(row, code_col, grand_total.get(code), text_bold_right)
            code_col += 1

        fp = io.BytesIO()
        workbook.save(fp)
        fp.seek(0)
        data = fp.read()
        fp.close()
        self.write({'file_data': base64.b64encode(data)})
        action = {
            'name': 'Journal Entries',
            'type': 'ir.actions.act_url',
            'url': "/web/content/?model=hr.payslip.run&id=" + str(self.id) + "&field=file_data&download=true&filename=Listado_de_nomina.xls",
            'target': 'self',
            }
        return action