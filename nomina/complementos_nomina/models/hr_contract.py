# -*- coding: utf-8 -*-

import pytz
from datetime import date
from datetime import datetime, timedelta
from odoo import api, fields, models
import logging
_logger = logging.getLogger(__name__)

class HrContract(models.Model):
    _inherit = 'hr.contract'

    def get_bono_vales_despensa(self):
        # Se requiere obtener siempre la segunda semana de cada mes
        # Obtenemos la  fecha actual
        tz_mx = pytz.timezone('America/Mexico_City')
        today = datetime.now(tz_mx)
        current_year = today.strftime('%Y')
        current_month = today.strftime('%m')
        current_date = today.strptime((today.strftime('%Y') + '-' + today.strftime('%m') + '-' + today.strftime('%d')),
                                      '%Y-%m-%d')

        # Formamos el primer día del cada mes
        first_week_month = current_year + "-" + current_month + "-01"
        # convertimos la variable de inicio del mes a tipo fecha
        dt = datetime.strptime(first_week_month, '%Y-%m-%d')
        # Obtenemos el primer de la semana
        r_week_start = dt - timedelta(days=dt.weekday())
        # print("Inicio semana", r_week_start.strftime('%d'))
        dias_sum = 7
        dias_sum_2 = 21
        if r_week_start.strftime('%m') != "02":
            if int(r_week_start.strftime('%d')) >= 25 and (int(r_week_start.strftime('%d')) == 29 or int(r_week_start.strftime('%d')) < 29):
                dias_sum = 14
                dias_sum_2 = 28

        # Sumamos una semana al incio de sem
        week_start = r_week_start + timedelta(days=dias_sum)
        # Sumamos ahora 6 días para obtener el fin de sem
        week_end_sem1 = week_start + timedelta(days=6)

        # Sumamos una semana al incio de sem
        week_start_sem_2 = r_week_start + timedelta(days=dias_sum_2)
        # Sumamos ahora 6 días para obtener el fin de sem
        week_end_sem2 = week_start_sem_2 + timedelta(days=6)

        # current_date = today.strptime("2021-02-03", '%Y-%m-%d')
        # Obtener los días de antiguedad
        now_date = today.strftime('%Y-%m-%d')
        v_start_date = self.date_start.strftime('%Y-%m-%d')
        start_date = datetime.strptime(v_start_date, '%Y-%m-%d')
        today = datetime.strptime(now_date, '%Y-%m-%d')

        dias_antiguedad = int((today - start_date) / timedelta(days=1))
        # print("Días antiguedad", dias_antiguedad)

        # Fecha de alta de la persona
        v_start_real_date = self.date_start.strftime('%Y-%m-%d')
        start_real_date = datetime.strptime(v_start_real_date, '%Y-%m-%d')

        if start_real_date < week_start:
            if current_date >= week_start and current_date <= week_end_sem1:
                self.pay_pantry_vouchers = True
            elif current_date >= week_start_sem_2 and current_date <= week_end_sem2:
                self.pay_pantry_vouchers = True
            else:
                self.pay_pantry_vouchers = False
        else:
            self.pay_pantry_vouchers = False

    def get_bono_asistencia(self):
        #Se requiere obtener siempre la segunda semana de cada mes
        #Obtenemos la  fecha actual
        tz_MX = pytz.timezone('America/Mexico_City')
        today = datetime.now(tz_MX)
        current_year = today.strftime('%Y')
        current_month = today.strftime('%m')
        current_date = today.strptime((today.strftime('%Y') + '-' + today.strftime('%m') + '-' + today.strftime('%d')),
                                      '%Y-%m-%d')
        _logger.error('currenmont: %s', current_month)
        #Formamos el primer día del cada mes
        first_week_month = current_year + "-" + current_month + "-01"
        #convertimos la variable de inicio del mes a tipo fecha
        dt = datetime.strptime(first_week_month, '%Y-%m-%d')
        #Obtenemos el primer de la semana
        r_week_start = dt - timedelta(days=dt.weekday())

        #Sumamos una semana al incio de sem
        week_start = r_week_start + timedelta(days=7)
        #Sumamos ahora 6 días para obtener el fin de sem
        week_end = week_start + timedelta(days=6)

        # Obtener los días de antiguedad
        now_date = today.strftime('%Y-%m-%d')
        v_start_date = self.date_start.strftime('%Y-%m-%d')
        start_date = datetime.strptime(v_start_date, '%Y-%m-%d')
        v_today = datetime.strptime(now_date, '%Y-%m-%d')

        dias_antiguedad = int((v_today - start_date) / timedelta(days=1))

        if dias_antiguedad >= 30:
            if current_date >= week_start and current_date <= week_end:
                last_month = 0
                last_year = 0
                if current_month == '01':
                    last_month = 12
                    last_year = int(current_year) - 1
                    _logger.info('mes correcto')
                else:
                    last_month = int(current_month) - 1
                    last_year = current_year

                last_month = str(last_month)
                last_year = str(last_year)

                start_date_last_month = str(last_year) + "-" + last_month.rjust(2, '0') + "-01"

                if last_month == 1 or last_month == 3 or last_month == 5 or last_month == 7 or last_month == 8 or last_month == 10 or last_month == 12:
                    end_date_last_month = last_year + "-" + last_month.rjust(2, '0') + "-31"
                elif last_month == 4 or last_month == 6 or last_month == 9 or last_month == 11:
                    end_date_last_month = last_year + "-" + last_month.rjust(2, '0') + "-30"
                else:
                    end_date_last_month = last_year + "-" + last_month.rjust(2, '0') + "-28"

                incidencias = 0

                #print("fecha inicio mes anterior:", start_date_last_month)
                #print("fecha final mes anterior:", end_date_last_month)

                line_faltas = self.env['faltas.nomina'].search(
                    [('employee_id', '=', self.employee_id.id), ('fecha_inicio', '>=', start_date_last_month),
                     ('fecha_inicio', '<=', end_date_last_month), ('state', '=', 'done'),
                     ('tipo_de_falta', 'in', ['Injustificada', 'retardo', 'Justificada sin goce de sueldo'])],
                    order='id desc', limit=1)

                if line_faltas:
                    incidencias += 1

                line_ret = self.env['retardo.nomina'].search(
                    [('employee_id', '=', self.employee_id.id), ('state', '=', 'done'),
                     ('fecha', '>=', start_date_last_month), ('fecha', '<=', end_date_last_month)],
                    order='id desc', limit=1)

                if line_ret:
                    incidencias += 1

                #line_inc = self.env['incapacidades.nomina'].search(
                #    [('employee_id', '=', self.employee_id.id), ('state', '=', 'done'),
                #     ('fecha', '>=', start_date_last_month), ('fecha', '<=', end_date_last_month)],
                #    order='id desc', limit=1)

                #if line_inc:
                #    incidencias += 1

                if incidencias == 0:
                    self.pay_attendance_bonus = True
                else:
                    self.pay_attendance_bonus = False
            else:
                self.pay_attendance_bonus = False
        else:
            self.pay_attendance_bonus = False

    def get_bono_lavanderia(self):
        #Se requiere obtener siempre la segunda semana de cada mes
        #Obtenemos la  fecha actual
        tz_MX = pytz.timezone('America/Mexico_City')
        today = datetime.now(tz_MX)
        current_year = today.strftime('%Y')
        current_month = today.strftime('%m')
        current_date = today.strptime((today.strftime('%Y') + '-' + today.strftime('%m') + '-' + today.strftime('%d')),
                                      '%Y-%m-%d')

        #Formamos el primer día del cada mes
        first_week_month = current_year + "-" + current_month + "-01"
        #convertimos la variable de inicio del mes a tipo fecha
        dt = datetime.strptime(first_week_month, '%Y-%m-%d')
        #Obtenemos el primer de la semana
        r_week_start = dt - timedelta(days=dt.weekday())

        #Sumamos una semana al incio de sem
        week_start = r_week_start + timedelta(days=7)
        #Sumamos ahora 6 días para obtener el fin de sem
        week_end = week_start + timedelta(days=6)

        #current_date = today.strptime("2021-02-24", '%Y-%m-%d')
        # Obtener los días de antiguedad
        now_date = today.strftime('%Y-%m-%d')
        v_start_date = self.date_start.strftime('%Y-%m-%d')
        start_date = datetime.strptime(v_start_date, '%Y-%m-%d')
        v_today = datetime.strptime(now_date, '%Y-%m-%d')

        dias_antiguedad = int((v_today - start_date) / timedelta(days=1))

        if dias_antiguedad >= 30:
            if current_date >= week_start and current_date <= week_end:
                #if self.department_id.parent_id != "340" and self.department_id.name != "INSPECCION VISUAL" and self.department_id.name != "TECNOLÓGIA DE MAQUINARIA":
                if self.department_id.parent_id != "340":
                    if self.job_id.name == 'OPERADOR' or self.job_id.name == 'ASISTENTE' or self.job_id.name == 'OPERADOR LIDER' or self.job_id.name == 'AUXILIAR':
                        self.first_week_month = True
                    else:
                        self.first_week_month = False
                else:
                    self.first_week_month = False
            else:
                self.first_week_month = False
        else:
            self.first_week_month = False

    def get_antiquity_years(self):
        v_start_date = self.date_start.strftime('%Y-%m-%d')
        if self.date_end:
            v_end_date = self.date_end.strftime('%Y-%m-%d')

            start_date = datetime.strptime(v_start_date, '%Y-%m-%d')
            end_date = datetime.strptime(v_end_date, '%Y-%m-%d')

            days = (end_date - start_date) / timedelta(days=365)
            self.antiquity_years = round(days, 2)
        else:
            self.antiquity_years = 0.00

    def get_antiquity_date(self):
        today = datetime.now()
        current_year = today.strftime('%Y')
        current_date = today.strftime('%Y-%m-%d')

        start_date = self.date_start.strftime('%Y-%m-%d')
        a_start_date = start_date.split("-")
        v_start_date = current_year + "-" + a_start_date[1] + "-" + a_start_date[2]
        f_start_date = datetime.strptime(v_start_date, '%Y-%m-%d')

        dt = datetime.strptime(current_date, '%Y-%m-%d')

        week_start = dt - timedelta(days=dt.weekday())
        r_week_start = week_start + timedelta(days=-7)
        week_end = r_week_start + timedelta(days=6)

        if f_start_date >= r_week_start and f_start_date <= week_end:
            self.anniversary_year = True
        else:
            self.anniversary_year = False

    def _calculate_vacations(self):
        today = datetime.now()
        current_year = today.strftime('%Y')
        current_date = today.strftime('%Y-%m-%d')

        v_start_date = self.date_start.strftime('%Y-%m-%d')

        #Obtener los años de antiguedad
        start_date = datetime.strptime(v_start_date, '%Y-%m-%d')
        today = datetime.strptime(current_date, '%Y-%m-%d')

        years_antiquity = int((today - start_date) / timedelta(days=365))
        #print("Años antiguedad:", years_antiquity)

        #obetenes la fecha de inicio en el año actual
        a_start_date = v_start_date.split("-")
        v_start_date = current_year + "-" + a_start_date[1] + "-" + a_start_date[2]
        f_start_date = datetime.strptime(v_start_date, '%Y-%m-%d')

        if f_start_date <= today:
            if self.active_update_year:
                self.last_year_update = current_year
                #print("no esta actualizando")
            else:
                vac_x_anti = 0.00

                line = self.env['tablas.antiguedades.line'].search([('form_id','=',self.tablas_cfdi_id.id),('antiguedad','<=', years_antiquity)], order='antiguedad desc', limit=1)
                if line:
                    vac_x_anti = line.vacaciones

                #print("Días vac", vac_x_anti)

                #Obtiene el total de las vacaciones al año actual
                current_vac = 0
                line_vac = self.env['tablas.vacaciones.line'].search(
                    [('form_id', '=', self.id), ('ano', '<=', current_year)],
                    order='id desc', limit=1)
                if line_vac:
                    current_vac += line_vac.dias

                #print("vacaciones tabla", current_vac)
                #Obtiene el acumulado de las vacaciones pendientes más por ley
                total_vac = current_vac + vac_x_anti

                for line in self.tabla_vacaciones:
                    self.tabla_vacaciones = [(2, line.id)]

                """self.write(
                    {'tabla_vacaciones': [(0, 0, {'form_id': self.id, 'ano': current_year, 'dias': total_vac})]})"""

                self.active_update_year = True
                self.last_year_update = current_year
        else:
            self.last_year_update = current_year
            self.active_update_year = False

    @api.depends('date_start')
    def _compute_fch_antiguedad(self):
        for record in self:
            if not record.fch_antiguedad and record.date_start:
                record.write({'fch_antiguedad': record.date_start})
            record.fch_antiguedad_automatico = True

    infonavit_mov_perm = fields.Boolean(string='Infonavit movimiento permanente')
    infonavit_mov_perm_monto = fields.Float(
        string='Monto Infonavit movimiento permanente',
        digits=(12, 4)
    )
    fch_antiguedad = fields.Date(string=u'Fecha antigüedad reconocida')
    fch_antiguedad_automatico = fields.Boolean(compute=_compute_fch_antiguedad)
    transporte = fields.Boolean(string='Transporte')
    transporte_monto = fields.Float(
        string='Monto Transporte',
        digits=(12, 4)
    )
    retroactivo = fields.Boolean(string='Retroactivo')
    retroactivo_monto = fields.Float(
        string='Monto Retroactivo',
        digits=(12, 4)
    )
    seguro_vivienda = fields.Boolean(string='Incluir pago de seguro de vivienda')

    pay_pantry_vouchers = fields.Boolean(string="Pay pantry vouchers", compute="get_bono_vales_despensa")
    first_week_month = fields.Boolean(string="First week month", compute="get_bono_lavanderia")
    anniversary_year = fields.Boolean(string="Anniversary year", compute="get_antiquity_date")
    antiquity_years = fields.Float(string="Antiquity years", compute="get_antiquity_years")
    payroll_number_employee = fields.Char(string="Payroll number employee", related="employee_id.no_empleado")
    intern_inability = fields.Boolean(string="Intern inability")
    days_intern_inability = fields.Float(string="Days intern inability", defauult=0.0)
    porcentage_intern_inability = fields.Float(string="Porcentage intern inability", default=0.0)

    quality_bonus = fields.Float(string='Quality Bonus ($)', default=0.00)
    laundry_bonus = fields.Boolean(string='Quality Laundry')
    loyalty_bonus = fields.Boolean(string='Loyalty Bonus')
    # Quitar bonus en automatico
    apply_bonus_automatically = fields.Boolean(string="Apply bonus automatically")
    pay_attendance_bonus = fields.Boolean('Pay attendance bonus', compute="get_bono_asistencia")

    last_year_update = fields.Char(string="Last year update", compute="_calculate_vacations")
    active_update_year = fields.Boolean(string="Active update year", store=True)
    bono_asistencia_porcentaje = fields.Float(string='% Bono')
    bono_puntualidad_porcentaje = fields.Float(string='% Bono')
    bono_retroactivo_porcentaje = fields.Float(string='% Bono')
    

   

    @api.depends('date_start')
    def _compute_antiguedad_anos(self):
        if self.date_start:
            date_start = self.fch_antiguedad
            today = datetime.today().date()
            diff_date = today - date_start
            years = diff_date.days / 365.0
            self.antiguedad_anos = int(years)
            
    @api.model
    def _difference_date(self, init_date):
        fmt = '%Y-%m-%d'
        start_date = init_date.strftime(fmt)
        end_date = datetime.now(pytz.timezone('America/Mexico_City')).strftime(fmt)
        # Pasamos a una lista cada fecha para poder manipular cada dato
        a_end_date = end_date.split('-')
        a_start_date = start_date.split('-')
        # Evaluamos a tiempo las dos fechas para validar si una es mayor a otra
        d1 = datetime.strptime(start_date, fmt)
        d2 = datetime.strptime(end_date, fmt)
        # Validamos si la fecha actual es mayor a la fecha de alta
        if d2 > d1:
            date1 = datetime(int(a_start_date[0]), int(a_start_date[1]), int(a_start_date[2]))
            date2 = datetime(int(a_end_date[0]), int(a_end_date[1]), int(a_end_date[2]))

            diff = relativedelta.relativedelta(date2, date1)

            year = diff.years
            months = diff.months
            days = diff.days

            return str(year) + " AÑOS " + str(months) + " MESES " + str(days) + " DÍAS"
        else:
            return "0 AÑOS 0 MESES 0 DÍAS"