# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import ValidationError
from odoo.exceptions import UserError
from datetime import datetime
from datetime import datetime, timedelta
import logging
_logger = logging.getLogger(__name__)


class TablasAntiguedadesLine(models.Model):
    _inherit = 'tablas.antiguedades.line'

    factor_integracion = fields.Float(string='Factor de Integración', compute='calculo_factor_ingreso', store=True, digits=(12,4))


    @api.depends('aguinaldo', 'factor_integracion', 'vacaciones', 'prima_vac', 'antiguedad')
    def calculo_factor_ingreso(self):
        factor_aguinaldo = 0.0
        factor_vaciones = 0.0
        for rec in self:
            dias_año = 365
            factor_aguinaldo = rec.aguinaldo / dias_año
            factor_vaciones = (rec.vacaciones * (rec.prima_vac / 100)) / dias_año
            rec.factor_integracion = float(factor_aguinaldo) + float(factor_vaciones) + 1.0


class Contract(models.Model):
    _inherit = "hr.contract"


    def actualiza_sbc(self):
        if self.date_start: 
            today = datetime.today().date()
            diff_date = (today - self.date_start + timedelta(days=1)).days
            years = diff_date /365.0
           

        for rec in self:
            if years <= 1.0:
                factor_integracion = self.env['tablas.antiguedades.line'].search([('antiguedad', '=', 1.0)])
            else:
                years = int(years)
                factor_integracion = self.env['tablas.antiguedades.line'].search([('antiguedad', '=', years)])
            if years >= 13.0:
                factor_integracion = self.env['tablas.antiguedades.line'].search([('antiguedad', '=', 13.0)])
            

            rec.sueldo_base_cotizacion = rec.sueldo_diario * factor_integracion.factor_integracion
            rec.sueldo_diario_integrado = rec.sueldo_diario * factor_integracion.factor_integracion

    @api.onchange('wage')
    def _compute_sueldo(self):
        if self.wage:            
            values = {
            'sueldo_diario': self.wage/self.tablas_cfdi_id.imss_mes,
            'sueldo_hora': self.wage/self.tablas_cfdi_id.imss_mes/8,
            'sueldo_diario_integrado': self.calculate_sueldo_diario_integrado(),
            'sueldo_base_cotizacion': self.calculate_sueldo_base_cotizacion(),
            }
            self.update(values)

    @api.model
    def calculate_sueldo_base_cotizacion(self): 
        if self.date_start: 
            today = datetime.today().date()
            diff_date = (today - self.date_start + timedelta(days=1)).days
            years = diff_date /365.0
           
            tablas_cfdi = self.tablas_cfdi_id 
            if not tablas_cfdi: 
                tablas_cfdi = self.env['tablas.cfdi'].search([],limit=1) 
            if not tablas_cfdi:
                return 
            if years < 1.0: 
                #tablas_cfdi_lines = tablas_cfdi.tabla_antiguedades.filtered(lambda x: x.antiguedad >= years).sorted(key=lambda x:x.antiguedad) 
                tablas_cfdi_lines = self.env['tablas.antiguedades.line'].search([('antiguedad', '=', 1.0), ('form_id', '=', self.tablas_cfdi_id.id)])
            else: 
                years = int(years)
                 
                tablas_cfdi_lines = self.env['tablas.antiguedades.line'].search([('antiguedad', '=', years), ('form_id', '=', self.tablas_cfdi_id.id)])
                #tablas_cfdi_lines = tablas_cfdi.tabla_antiguedades.filtered(lambda x: x.antiguedad <= years).sorted(key=lambda x:x.antiguedad, reverse=True) 
            if years >= 13.0:

                factor_integracion = self.env['tablas.antiguedades.line'].search([('antiguedad', '=', 13.0)])
            if not tablas_cfdi_lines: 
                return             
            tablas_cfdi_line = tablas_cfdi_lines[0]
            max_sdi = tablas_cfdi.uma * 25
            self.sueldo_diario = self.wage/self.tablas_cfdi_id.imss_mes           
            sdi = self.sueldo_diario * tablas_cfdi_lines.factor_integracion            
            if sdi > max_sdi:
                sueldo_base_cotizacion = max_sdi
            else:
                sueldo_base_cotizacion = sdi
        else: 
            sueldo_base_cotizacion = 0
        return sueldo_base_cotizacion

    @api.model
    def calculate_sueldo_diario_integrado(self): 
        if self.date_start: 
            today = datetime.today().date()
            diff_date = (today - self.date_start + timedelta(days=1)).days
            years = diff_date /365.0
            #_logger.info('years ... %s', years)
            tablas_cfdi = self.tablas_cfdi_id 
            if not tablas_cfdi: 
                tablas_cfdi = self.env['tablas.cfdi'].search([],limit=1) 
            if not tablas_cfdi:
                return 
            if years < 1.0: 
                #tablas_cfdi_lines = tablas_cfdi.tabla_antiguedades.filtered(lambda x: x.antiguedad >= years).sorted(key=lambda x:x.antiguedad) 
                tablas_cfdi_lines = self.env['tablas.antiguedades.line'].search([('antiguedad', '=', 1.0), ('form_id', '=', self.tablas_cfdi_id.id)])
            else:
                years = int(years)
                 
                tablas_cfdi_lines = self.env['tablas.antiguedades.line'].search([('antiguedad', '=', years), ('form_id', '=', self.tablas_cfdi_id.id)])
 
                #tablas_cfdi_lines = tablas_cfdi.tabla_antiguedades.filtered(lambda x: x.antiguedad <= years).sorted(key=lambda x:x.antiguedad, reverse=True) 
            if years >= 13.0:

                factor_integracion = self.env['tablas.antiguedades.line'].search([('antiguedad', '=', 13.0)])
            if not tablas_cfdi_lines: 
                return 
            tablas_cfdi_line = tablas_cfdi_lines[0]
            max_sdi = tablas_cfdi.uma * 25
            self.sueldo_diario = self.wage/self.tablas_cfdi_id.imss_mes
            sdi = self.sueldo_diario * tablas_cfdi_lines.factor_integracion
            sueldo_diario_integrado = sdi
        else: 
            sueldo_diario_integrado = 0
        return sueldo_diario_integrado


class TablasCFDI(models.Model):
    _inherit = 'tablas.cfdi'


    salario_min_frontera = fields.Float('Salario mínimo ZLFN')
    sd_n = fields.Boolean('SD a días naturales')
    sd_anual = fields.Boolean('SD Anual')
    days = fields.Float('Días', default=0)
    isn_lines = fields.One2many('tablas.isn', 'form_id', copy=True)

    @api.onchange('sd_anual', 'sd_n')
    def dias_sd(self):

        if self.sd_n == True:
            self.imss_mes = 30
        if self.sd_anual == True:
            self.imss_mes = 30.4
        if self.sd_anual == False and self.sd_n == False:
            self.imss_mes = 0
        

class TablasSubsidiolLine(models.Model):
    _name = 'tablas.isn'
    

    form_id = fields.Many2one('tablas.cfdi', string='ISN', required=True)
    region = fields.Many2one('res.country.state.sat.code', string='Región', domain="[('country_sat_code', '=', 'MEX')]") 
    porcentaje = fields.Float('Porcentaje') 
