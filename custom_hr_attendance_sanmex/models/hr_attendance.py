
# -*- coding: utf-8 -*-
from odoo import models, fields, api, _


class HrAttendance(models.Model):
    _inherit = 'hr.attendance'
    
    department_id = fields.Many2one(store=True)
    
