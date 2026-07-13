# -*- coding: utf-8 -*-

from odoo import api, fields, models

class HrEmployee(models.Model):
    _inherit = 'hr.employee'

    certificate_dos = fields.Selection([
        ('graduate', 'Licenciatura'),
        ('basics', 'Primaria'),
        ('bachelor', 'Secundaria'),
        ('master', 'Bachillerato'),
        ('doctor', 'Doctorado'),
        ('other', 'Otro'),
    ], 'Certificate Level', default='other', groups="hr.group_hr_user", tracking=True)

    # registro_patronal = fields.Char(string='Registro patronal', default="B4746081107")
    registro_patronal_nuevo = fields.Many2one(
        comodel_name='registro.patronal',
        string='Registro patronal',
    )
    work_location = fields.Char(string="Work Location", default="CASTRO DEL RIO")
    phone_two = fields.Char(string="Phone")
    loan_request = fields.Integer(default=100)
    fouls_employee_ids = fields.One2many('faltas.nomina', 'employee_id', string='Fouls Payroll', readonly=True)
    vacations_ids = fields.One2many('vacaciones.nomina', 'employee_id', string='Vacation Payroll', readonly=True)
    aditional_hour_ids = fields.One2many('horas.nomina', 'employee_id', string='Aditional Hours Payroll', readonly=True)
    delays_ids = fields.One2many('retardo.nomina', 'employee_id', string='Delays Payroll', readonly=True)
    inability_ids = fields.One2many('incapacidades.nomina', 'employee_id', string='Inability Payroll', readonly=True)
    holidays_days_ids = fields.One2many('dias.feriados', 'employee_id', string='Holiday Days Payroll', readonly=True)
    es_extranjero = fields.Boolean(string='Es extranjero')
    
    @api.onchange('no_empleado')
    def onchange_payroll_number(self):
        self.no_employee = self.no_empleado
        #print("Actualizo datos")

    @api.onchange('no_employee')
    def onchange_payroll_number_two(self):
        self.no_empleado = self.no_employee

    @api.model
    def create(self, vals):
        seq_obj = self.env['ir.sequence']
        next_number = seq_obj.next_by_code('sequence.employee')
        vals['no_empleado'] = next_number
        vals['no_employee'] = next_number
        return super(HrEmployee, self).create(vals)

    @api.onchange('registro_patronal_nuevo')
    def _onchange_registro_patronal_nuevo(self):
        self.registro_patronal = self.registro_patronal_nuevo.name