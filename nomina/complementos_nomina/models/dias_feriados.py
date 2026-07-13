# -*- coding: utf-8 -*-

import pytz
from datetime import datetime

from odoo import models, fields, api
from odoo.exceptions import UserError


class DiasFeriados(models.Model):
    _inherit = 'dias.feriados'

    def action_validar(self):
        if self.fecha:
            fecha = self.fecha
            date_from = fecha.strftime("%Y-%m-%d") + ' 00:00:00'
            date_to = fecha.strftime("%Y-%m-%d") + ' 23:59:59'
        else:
            date_from = datetime.today().strftime("%Y-%m-%d")
            date_to = date_from + ' 20:00:00'
            date_from += ' 06:00:00'

        timezone = self._context.get('tz')
        if not timezone:
            timezone = self.env.user.partner_id.tz or 'UTC'

        local = pytz.timezone(timezone)
        naive_from = datetime.strptime(date_from, "%Y-%m-%d %H:%M:%S")
        local_dt_from = local.localize(naive_from, is_dst=None)
        utc_dt_from = local_dt_from.astimezone(pytz.utc)
        date_from = utc_dt_from.strftime("%Y-%m-%d %H:%M:%S")

        naive_to = datetime.strptime(date_to, "%Y-%m-%d %H:%M:%S")
        local_dt_to = local.localize(naive_to, is_dst=None)
        utc_dt_to = local_dt_to.astimezone(pytz.utc)
        date_to = utc_dt_to.strftime("%Y-%m-%d %H:%M:%S")

        if self.tipo == 'doble':
            leave_type = self.env['hr.leave.type'].search([('name', '=', 'DFES')])
            if not leave_type:
                raise UserError(
                    'No existe una configuración de Tipo de Ausencia con el nombre DFES para esta compañía.')
        else:
            leave_type = self.env['hr.leave.type'].search([('name', '=', 'DFES_3')])
            if not leave_type:
                raise UserError(
                    'No existe una configuración de Tipo de Ausencia con el nombre DFES_3 para esta compañía.')

        nombre = 'Feriado_' + self.name
        registro_falta = self.env['hr.leave'].search([('name', '=', nombre)], limit=1)
        if registro_falta:
            registro_falta.write({'date_from': date_from,
                                  'date_to': date_to,
                                  'employee_id': self.employee_id.id,
                                  'holiday_status_id': leave_type and leave_type.id,
                                  'state': 'validate',
                                  })
        else:
            holidays_obj = self.env['hr.leave']
            vals = {'date_from': date_from,
                    'holiday_status_id': leave_type and leave_type.id,
                    'employee_id': self.employee_id.id,
                    'name': 'Feriado_' + self.name,
                    'date_to': date_to,
                    'state': 'confirm',
                    }

            holiday = holidays_obj.new(vals)
            #holiday._onchange_employee_id()
            #holiday._onchange_leave_dates()
            vals.update(holiday._convert_to_write({name: holiday[name] for name in holiday._cache}))
            vals.update({'holiday_status_id': leave_type and leave_type.id})
            feriado = self.env['hr.leave'].create(vals)
            feriado.action_validate()
        self.write({'state': 'done'})
        return
