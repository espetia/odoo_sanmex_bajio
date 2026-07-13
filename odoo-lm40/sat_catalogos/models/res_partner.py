# -*- coding: utf-8 -*-

from odoo import api, fields, models, _, tools
from datetime import datetime
import time
import logging
_logger = logging.getLogger(__name__)




class ResPartner(models.Model):
    _name = 'res.partner'
    _inherit = 'res.partner'
    
    persona_fisica =  fields.Boolean('Persona Fisica')
    curp = fields.Char(string="CURP")
    customer = fields.Boolean(string='Cliente', default=True,
                               help="Check this box if this contact is a customer.")
    supplier = fields.Boolean(string='Proveedor',
                               help="Check this box if this contact is a vendor. "
                               "If it's not checked, purchase people will not see it when encoding a purchase order.")
    num_reg_trib =  fields.Char('NumRegIdTrib', size=40)
    street_reference =  fields.Char('Referencias', size=128)
    sat_municipio_id = fields.Many2one('res.country.township.sat.code','Municipio')
    sat_localidad_id = fields.Many2one('res.country.locality.sat.code','Localidad')
    sat_codigopostal_id = fields.Many2one('res.country.zip.sat.code','CP Sat')
    colonia_sat_id = fields.Many2one('res.colonia.zip.sat.code','Colonia Sat')
    country_code_rel = fields.Char('Codigo Pais', related="country_id.code")
    
    company_type2 = fields.Selection(string='Tipo Compañia',
        selection=[('person', 'Contacto'), ('company', 'Compañia'),('physical_person', 'Persona Fisica')], readonly=False, default="person")

    regimen_fiscal_id = fields.Many2one('sat.regimen.fiscal', string="Régimen Fiscal", required=True)

    uso_cfdi_id = fields.Many2one('sat.uso.cfdi', 'Uso CFDI', required=True) 
    vat_split =  fields.Char('VAT Split')
    tipo_contribuyente = fields.Many2one('contribuyente', string='Tipo Contribuyente')
    tipo_tercero = fields.Selection([('04', ' 04 - Proveedor Nacional'),
                                        ('05', ' 05 - Proveedor Extranjero'),
                                        ('15', ' 15 - Proveedor Global')],
                                        string='Tipo de Proveedor')
    tipo_operacion = fields.Selection([('03', ' 03 - Provision de Servicios Profesionales'),
                                          ('06', ' 06 - Arrendamientos'),
                                          ('85', ' 85 - Otros')],
                                            string='Tipo de Operación')
    paises_diot = fields.Selection([
        ('AR', 'AR - Argentina'),
        ('AT', 'AT - Austria'),
        ('AU', 'AU - Australia'),
        ('BE', 'BE - Belgica'),
        ('BC', 'BC - Belice'),
        ('BO', 'BO - Bolivia'),
        ('BR', 'BR - Brasil'),
        ('CA', 'CA - Canada'),
        ('CL', 'CL - Chile'),
        ('CM', 'CM - Camerun'),
        ('CN', 'CN - China'),
        ('CO', 'CO - Colombia'),
        ('CR', 'CR - República de Costa Rica'),
        ('CU', 'CU - Cuba'),
        ('DM', 'DM - República Dominicana'),
        ('DZ', 'DZ - Argelia'),
        ('EC', 'EC - Ecuador'),
        ('EG', 'EG - Egipto'),
        ('EH', 'EH - Sahara del Oeste'),
        ('EO', 'EO - Estado Independiente de Samoa Occidental'),
        ('ES', 'ES - España'),
        ('ET', 'ET - Etiopia'),
        ('GR', 'GR - Grecia'),
        ('GT', 'GT - Guatemala'),
        ('GU', 'GU - Guam'),
        ('GW', 'GW - Guinea Bissau'),
        ('GY', 'GY - República de Guyana'),
        ('GZ', 'GZ - Islas de Guernesey, Jersey, Alderney, '\
            'Isla Great Sark, Herm, Little Sark, Berchou, Jethou, '\
            'Lihou (Islas del Canal)'),
        ('HK', 'HK - Hong Kong'),
        ('HM', 'HM - Islas Heard and Mc Donald'),
        ('HN', 'HN - República de Honduras'),
        ('HT', 'HT - Haiti'),
        ('HU', 'HU - Hungaria'),
        ('ID', 'ID - Indonesia'),
        ('IE', 'IE - Irlanda'),
        ('IH', 'IH - Isla del Hombre'),
        ('IL', 'IL - Israel'),
        ('IN', 'IN - India'),
        ('IO', 'IO - Territorio Británico en el Océano Indico'),
        ('IP', 'IP - Islas Pacifico'),
        ('IQ', 'IQ - Iraq'),
        ('IR', 'IR - Iran'),
        ('IS', 'IS - Islandia'),
        ('IT', 'IT - Italia'),
        ('JM', 'JM - Jamaica'),
        ('JO', 'JO - Reino Hachemita de Jordania'),
        ('JP', 'JP - Japon'),
        ('KE', 'KE - Kenia'),
        ('KH', 'KH - Campuchea Democratica'),
        ('KI', 'KI - Kiribati'),
        ('KM', 'KM - Comoros'),
        ('KN', 'KN - San Kitts'),
        ('KP', 'KP - República Democratica de Corea'),
        ('KR', 'KR - República de Corea'),
        ('KW', 'KW - Estado de Kuwait'),
        ('KY', 'KY - Islas Caiman'),
        ('LA', 'LA - República Democratica de Laos'),
        ('LB', 'LB - Libano'),
        ('NL', 'NL - Holanda'),
        ('NO', 'NO - Noruega'),
        ('NP', 'NP - Nepal'),
        ('NR', 'NR - República de Nauru'),
        ('NT', 'NT - Zona Neutral'),
        ('NU', 'NU - Niue'),
        ('NV', 'NV - Nevis'),
        ('NZ', 'NZ - Nueva Zelanda'),
        ('OM', 'OM - Sultanía de Omán'),
        ('PA', 'PA - República de Panamá'),
        ('PE', 'PE - Peru'),
        ('PY', 'PY - Paraguay'),
        ('SV', 'SV - El Salvador'),
        ('UA', 'UA - Ucrania'),
        ('UG', 'UG - Uganda'),
        ('UM', 'UM - Islas Menores alejadas de Estados Unidos'),
        ('US', 'US - Estados Unidos de América'),
        ('UY', ' UY- República Oriental del Uruguay'),
        ('VA', 'VA - Vaticano'),
        ('VE', 'VE - Venezuela'),
        ('XX', 'XX - Otro'),
        ('YD', 'YD - Yemen Democratica'),
        ('YE', 'YE - República del Yemen'),
        ('YU', 'YU - Paises de las EX- Yugoslavia'),
        ('ZA', 'ZA - Sudafrica'),
        ('ZC', 'ZC - Zona Especial Canaria'),
        ('ZM', 'ZM - Zambia'),
        ('ZO', 'ZO - Zona Libre de Ostrava'),
        ('ZR', 'ZR - Zaire'),
        ('ZW', 'ZW - Zimbawe'),
        ], 'País')
    nif_diot = fields.Char(string='Identificador Fiscal', size=100)
    nacionalidad = fields.Char('Nacionalidad', size=100)
    anticipo_proveedor = fields.Many2one('account.account', company_dependent=True,
                                        string="Cuenta de Anticipo proveedores ")
    anticipo_cliente = fields.Many2one('account.account', company_dependent=True,
                                        string="Cuenta de Anticipo clientes", domain="[('internal_type','=','receivable')]")

    customer_advance = fields.Float(string='Total Customer Advance')
    supplier_advance = fields.Float(string='Total Supplier Advance')
    envio_cfdi = fields.Boolean("Envío manual del CFDI")
    objimp_id = fields.Many2one('sat.objetoimp', string="Objeto de Impuesto")
    
   

    @api.constrains('rfc', 'name')
    def _check_coste_product(self):
        
        
        if self.rfc:
            
            if self.rfc == 'XAXX010101000':
                if self.name != 'PUBLICO EN GENERAL':           
                    raise UserError("Razón Social incorrecta para este RFC: 'XAXX010101000', Razón Social correcta 'PUBLICO EN GENERAL'")

    @api.onchange('regimen_fiscal_id', 'uso_cfdi_id')
    def _onchange_usocfdi(self):
        if self.regimen_fiscal_id == "":
            self.update({
                'uso_cfdi_id': False,
                
            })
            
        else:
            
                
            return {'domain': {'uso_cfdi_id': [('RegimenFiscalReceptor', 'ilike', self.regimen_fiscal_id.code)]}}
    

    @api.onchange('company_type2')
    def onchange_company_type(self):
        if self.company_type2 in ('company','physical_person'):
            self.company_type = 'company'
            self.is_company = True
            if self.company_type2 == 'physical_person':
                self.persona_fisica = True
        else:
            self.company_type = 'person'

    

    
    @api.onchange('sat_codigopostal_id')
    def onchange_zip_sat_id(self):
        if self.sat_codigopostal_id:
            self.zip = self.sat_codigopostal_id.code          
            

            state_sat_code = self.sat_codigopostal_id.state_sat_code            
            state_id = self.env['res.country.state'].search([('sat_code','=',state_sat_code)])            
            if state_id:
                self.state_id = state_id[0].id                
                self.country_id = state_id[0].country_id.id                

            colonia_sat_id = self.env['res.colonia.zip.sat.code'].search([('zip_sat_code_char','=',self.sat_codigopostal_id.code)])
            
            if colonia_sat_id:
                self.colonia_sat_id = colonia_sat_id[0].id

    @api.onchange('state_id')
    def onchange_domain_sat_list(self):
        domain = {}
        if self.state_id:                       
            township_ids = self.env['res.country.township.sat.code'].search([('state_sat_code','=',self.state_id.sat_code.code)])
            self.sat_municipio_id = township_ids.filtered(lambda r: r.code == self.sat_codigopostal_id.township_sat_code).id
            
            if township_ids:
                domain.update(
                    {
                        'sat_municipio_id':[('id','in',[x.id for x in township_ids])]
                    })
             
            locality_ids = self.env['res.country.locality.sat.code'].search([('state_sat_code','=',self.state_id.sat_code.code)])
            self.sat_localidad_id = locality_ids.filtered(lambda r: r.code == self.sat_codigopostal_id.locality_sat_code).id
            if locality_ids:
                domain.update(
                    {
                        'sat_localidad_id':[('id','in',[x.id for x in locality_ids])]
                    })        

        return {'domain': domain}

    
    @api.onchange ('country_id', 'tipo_contribuyente')
    def rfc_extra(self):         
        
        if self.country_id.code != 'MX' and self.tipo_contribuyente.code == '002':
            self.rfc = self.tipo_contribuyente.rfc
            
        else:
            self.rfc = ""
            if self.tipo_contribuyente.code == '003' and self.country_id.code == 'MX':
                self.rfc = self.tipo_contribuyente.rfc
            
                
            