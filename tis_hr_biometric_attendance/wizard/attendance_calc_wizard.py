# -*- coding: utf-8 -*-
# This module and its content is copyright of Technaureus Info Solutions Pvt. Ltd.
# - © Technaureus Info Solutions Pvt. Ltd 2020. All rights reserved.

from odoo import models, _
from datetime import datetime, timedelta
import logging
_logger = logging.getLogger(__name__)

class AttendanceWizard(models.TransientModel):
    _name = 'attendance.calc.wizard'
    _description = 'attendance calc wizard'

    def calculate_attendance(self):
        hr_attendance = self.env['hr.attendance']
        today = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        domain = [('punching_time', '<=', str(today)), ('is_calculated', '=', False)]
        attendance_log = self.env['attendance.log'].search(domain)
        _logger.info(str(attendance_log))
        employee_list = []
        check_in_old = 0
        for log in attendance_log:
            attd = self.check_in_check_out(log.employee_id.id, log.punching_time)
            if log.status == '0':
                #if not attd:
                atted_rec_tmp = self.env['hr.attendance'].search([('employee_id','=', log.employee_id.id),('check_out','>',today)])
                if not atted_rec_tmp:
                    hr_attendance.create({'employee_id': log.employee_id.id, 'check_in': log.punching_time})

            if log.status == '1':
                if len(attd) == 1:
                    attd.write({'check_out': log.punching_time})
                    check_in_old =0
                else:
                    att_var1 = hr_attendance.search([('employee_id','=',log.employee_id.id)])
                    if att_var1:
                        att_var1[-1].write({'check_out': log.punching_time})
                        check_in_old =0
            #if log.employee_id.id in employee_list:
            #    attd = self.check_in_check_out(log.employee_id.id, log.punching_time)
            #    attendance = self.env['hr.attendance'].search([('id', '=', attd.id)])
                #if log.status == '1':
                #    attendance.write({'check_out': log.punching_time})
            #    else:
                    #att_var1 = hr_attendance.search([('employee_id','=',log.employee_id.id)])
                    #if att_var1:
                    #    att_var1[-1].write({'check_out': log.punching_time})
            #        if log.status == '0':
            #            hr_attendance.create({'employee_id': log.employee_id.id, 'check_in': log.punching_time})
            #            employee_list.append(log.employee_id.id)

                #employee_list.remove(log.employee_id.id)
           # else:
            #    attd = self.check_in_check_out(log.employee_id.id, log.punching_time)
                #attendance = self.env['hr.attendance'].search([('id', '=', attd.id)])
            #    if log.status == '0':
            #        if not attd:
            #            atted_rec_tmp = self.env['hr.attendance'].search([('employee_id','=', log.employee_id.id),('check_out','>',today)])
            #            if not atted_rec_tmp:
            #                hr_attendance.create({'employee_id': log.employee_id.id, 'check_in': log.punching_time})
            #                employee_list.append(log.employee_id.id)
                #
                #if log.status == '1':
                #    _logger.info("log estatus es una entrada")
                #    if len(attd) == 1:
                #        attd.write({'check_out': log.punching_time})
                #    else:
                #        att_var1 = hr_attendance.search([('employee_id','=',log.employee_id.id)])
                #        if att_var1:
                #            att_var1[-1].write({'check_out': log.punching_time})
                #
                #if attendance and attendance.check_out is False:
                #    if log.status == '1':
                #        attendance.write({'check_out': log.punching_time})
                #else:
                #    if log.status == '0' :
                #        _logger.info("log estatus es una entrada")
                #        hr_attendance.create({'employee_id': log.employee_id.id, 'check_in': log.punching_time})
                #        employee_list.append(log.employee_id.id)
            log.is_calculated = True

    def check_in_check_out(self, emp_id, time):
        attendances = self.env['hr.attendance'].search([('employee_id', '=', emp_id), ('check_out', '=', False)])
        return attendances
        #if attendances:
            #return attendances.id
