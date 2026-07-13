# -*- coding: utf-8 -*-

import json
import base64
import requests
import json
import urllib
import traceback
import qrcode
import codecs
import os
import sys
from reportlab.graphics.barcode import createBarcodeDrawing
from lxml import etree
import pytz
import datetime
from datetime import timedelta, date
import io
from reportlab.lib.units import mm
from odoo.exceptions import UserError
from odoo import api, fields, models, _
import logging
_logger = logging.getLogger(__name__)


class HrPayslip(models.Model):
    _inherit = 'hr.payslip'

    #def timbrar_nomina(self):
    @api.model
    def do_something_with_xml_attachment(self, attach):

        return True

    def action_cfdi_nomina_generate(self):
        res = super(HrPayslip, self).to_json()

        login = {}
        webservice_url = self.env['ir.config_parameter'].sudo().get_param('webservice.url')
        multi_company = self.env['ir.config_parameter'].sudo().get_param('webservice.multi_company')
       
        
        if multi_company == False:
           
            login = {
            "rfc": self.env['ir.config_parameter'].sudo().get_param('webservice.rfc_web'),
            "clave": self.env['ir.config_parameter'].sudo().get_param('webservice.password')
            }
        else:
            _logger.info('condición aceptada')
            login = {
            "rfc": self.company_id.rfc_web_1,
            "clave": self.company_id.password_1
            }
        if webservice_url == 'test':
            url = self.env['ir.config_parameter'].sudo().get_param('webservice.url_name_prue')
        if webservice_url == 'product':
            url = self.env['ir.config_parameter'].sudo().get_param('webservice.url_name_produc')

        # ******** NUEVO XML ********
        emisor_rfc = str(base64.b64encode(bytes(res['emisor']['rfc'], 'utf-8')))
        emisor_nombre = str(base64.b64encode(bytes(res['emisor']['nombre_fiscal'], 'utf-8')))
        receptor_rfc = str(base64.b64encode(bytes(res['receptor']['rfc'], 'utf-8')))
        receptor_nombre = str(base64.b64encode(bytes(res['receptor']['nombre'], 'utf-8')))
        concepto_dsc = str(base64.b64encode(bytes(res['conceptos']['descripcion'], 'utf-8')))
        curp_receptor = str(base64.b64encode(bytes(res['nomina12Receptor']['Curp'], 'utf-8')))
        #curp_emisor = str(base64.b64encode(bytes(res['nomina12Emisor']['Curp'], 'utf-8')))
        antiguedad_receptor = str(base64.b64encode(bytes(res['nomina12Receptor']['Antiguedad'], 'utf-8')))
        departmento_receptor = str(base64.b64encode(bytes(res['nomina12Receptor']['Departamento'], 'utf-8')))
        puesto_receptor = str(base64.b64encode(bytes(res['nomina12Receptor']['Puesto'], 'utf-8')))
        #registropatronal = str(base64.b64encode(bytes(res['nomina12Emisor']['RegistroPatronal'], 'utf-8')))
        rfpatron = str(base64.b64encode(bytes(res['nomina12Emisor']['RfcPatronOrigen'], 'utf-8')))
        #conceptootros = str(base64.b64encode(bytes(res['otros_pagos']['otros_pagos'][0]['Concepto'], 'utf-8')))
        percepciones = res['percepciones']['lineas_de_percepcion_excentas']
        percepciones.extend(res['percepciones']['lineas_de_percepcion_grabadas'])
        concepto = 'Subsidio para el empleo efectivamente entregado al trabajador'
        #concepto = 'Prestamos'
        concepto = str(concepto).encode("utf-8")
        base64_dato = base64.b64encode(concepto)
        concepto_dec = base64_dato.decode("utf-8")
        if res['nomina12Emisor']['RegistroPatronal']:
            registropatronal = str(base64.b64encode(bytes(res['nomina12Emisor']['RegistroPatronal'], 'utf-8')))
            registrop = registropatronal[2:len(registropatronal)-1]
        else:
            registrop = ""
        


        if int(res['otros_pagos']['no_otros_pagos']) > 0:
            _logger.info('siotrospagos')
            if self.tipo_relacion and self.uuid_relacionado:
                nuevo_xml = {
                'localizacion-mx':
                 {
                     'Login': login,

                     'Documento': {
                         'Operacion': 'TIMBRAR',
                         'TipoDocumento': 'NOMINA',
                         'Comprobante': {
                             'Version': '3.3',
                             'Folio': res['factura']['folio'],
                             'Fecha': res['factura']['fecha_factura'].replace(' ', 'T'),
                             'Sello': '', 
                             'FormaPago': res['factura']['forma_pago'],

                             'NoCertificado': '',
                             'Certificado': '',
                             'CfdiRelacionados': {
                                 'CfdiRelacionado': {
                                     'UUID': self.uuid_relacionado,  
                                 },
                                 'TipoRelacion': self.tipo_relacion,  
                             },
                             'Moneda': res['factura']['moneda'],
                             'TipoDeComprobante': res['factura']['tipocomprobante'],
                             'MetodoPago': res['factura']['metodo_pago'],
                             'Exportacion': '01',
                             'LugarExpedicion': res['factura']['LugarExpedicion'],
                             'SubTotal': res['factura']['subtotal'], 
                             'Descuento': res['factura']['descuento'], 
                             'Total': res['factura']['total'],
                             'Emisor': {
                                 'Rfc': emisor_rfc[2:len(emisor_rfc)-1],
                                 'Nombre': emisor_nombre[2:len(emisor_nombre)-1],
                                 'RegimenFiscal': res['factura']['RegimenFiscal'],
                             },
                             'Receptor': {
                                 'Rfc': receptor_rfc[2:len(receptor_rfc)-1],
                                 'Nombre': receptor_nombre[2:len(receptor_nombre)-1],
                                 'UsoCFDI': 'CN01', #res['receptor']['uso_cfdi'],
                                 'RegimenFiscalReceptor': '605',                    
                                 'DomicilioFiscalReceptor': self.employee_id.address_home_id.sat_codigopostal_id.code,#res['factura']['LugarExpedicion'],
                             },
                             'Complemento': {
                                 'TimbreFiscaldigital': {
                                     'TimbreFiscaldigital': '',  
                                     'FechaTimbrado': '',  
                                     'NoCertificadoSAT': '',  
                                     'RfcProvCertif': '',  
                                     'SelloCFD': '',  
                                     'SelloSAT': '',  
                                     'UUID': '',  
                                     'Version': '',  
                                 },
                                 'Pagos': {
                                     'Version': '',  
                                 },
                             },
                             'Conceptos': {
                                 'Concepto': 
                                 [
                                 {
                                     'ClaveProdServ': res['conceptos']['ClaveProdServ'],
                                     'NoIdentificacion': '',  
                                     'Cantidad': res['conceptos']['cantidad'],
                                     'ClaveUnidad': res['conceptos']['ClaveUnidad'],
                                     'Descripcion': concepto_dsc[2:len(concepto_dsc)-1],
                                     'ValorUnitario': res['conceptos']['valorunitario'], 
                                     'Importe': res['conceptos']['importe'],
                                     'Descuento': res['conceptos']['descuento'],
                                     'ObjetoImp': '01',
                                 }],
                             },
                             'Complementos': [
                             {
                                 'Nomina12': {
                                     'Version': '1.2',  
                                     'TipoNomina': res['nomina12']['TipoNomina'],
                                     'FechaPago': res['nomina12']['FechaPago'],
                                     'FechaInicialPago': res['nomina12']['FechaInicialPago'],
                                     'FechaFinalPago': res['nomina12']['FechaFinalPago'],
                                     'NumDiasPagados': res['nomina12']['NumDiasPagados'],
                                     'PeriodicidadPago': res['nomina12Receptor']['PeriodicidadPago'],
                                     'TotalPercepciones': res['nomina12']['TotalPercepciones'],
                                     'TotalDeducciones': res['nomina12']['TotalDeducciones'],
                                     'TotalOtrosPagos': res['nomina12']['TotalOtrosPagos'],
                                     'Receptor': {
                                         'Curp': curp_receptor[2:len(curp_receptor)-1],#res['nomina12Receptor']['Curp'], codificar
                                         'NumSeguridadSocial': res['nomina12Receptor']['NumSeguridadSocial'] or "",
                                         'FechaInicioRelLaboral': res['nomina12Receptor']['FechaInicioRelLaboral'],
                                         'Antiguedad': antiguedad_receptor[2:len(antiguedad_receptor)-1],#res['nomina12Receptor']['Antiguedad'], codificar
                                         'TipoContrato': res['nomina12Receptor']['TipoContrato'],
                                         'Sindicalizado': 'No',  
                                         'PeriodicidadPago': res['nomina12Receptor']['PeriodicidadPago'],
                                         'TipoJornada': res['nomina12Receptor']['TipoJornada'],
                                         'TipoRegimen': res['nomina12Receptor']['TipoRegimen'],
                                         'NumEmpleado': res['nomina12Receptor']['NumEmpleado'],
                                         'RiesgoPuesto': res['nomina12Receptor']['RiesgoPuesto'] or "",
                                         'Departamento': departmento_receptor[2:len(departmento_receptor)-1],#res['nomina12Receptor']['Departamento'], codificar
                                         'Puesto': puesto_receptor[2:len(puesto_receptor)-1],#res['nomina12Receptor']['Puesto'], codificar
                                         'SalarioBaseCotApor': res['nomina12Receptor']['SalarioBaseCotApor'],
                                         'SalarioDiarioIntegrado': res['nomina12Receptor']['SalarioDiarioIntegrado'],
                                         'ClaveEntFed': res['nomina12Receptor']['ClaveEntFed'],
                                     },
                                     'Emisor':{

                                            'RegistroPatronal': registrop, #registropatronal[2:len(registropatronal)-1] or "",#res['nomina12Emisor']['RegistroPatronal'],
                                            'RfcPatronOrigen': rfpatron[2:len(rfpatron)-1],#res['nomina12Emisor']['RfcPatronOrigen'],
                                            #'Curp': curp_emisor[2:len(curp_emisor)-1] or '',
                                     },

                                      'OtrosPagos': { 
                                             'OtroPago': {
                                                 'TipoOtroPago': res['otros_pagos']['otros_pagos'][0]['TipoOtrosPagos'],
                                                 'Clave': res['otros_pagos']['otros_pagos'][0]['TipoOtrosPagos'],
                                                 'Concepto': res['otros_pagos']['otros_pagos'][0]['Concepto'],
                                                 'Importe': res['otros_pagos']['otros_pagos'][0]['ImporteExento'],
                                                 'SubsidioAlEmpleo': {
                                                     'SubsidioCausado': self.subsidio_periodo,
                                                 },
                                                 
                                             }
                                         },
                                     'Percepciones': {
                                         'TotalSueldos': res['percepciones']['Totalpercepcion']['TotalSueldos'],
                                         'TotalGravado': res['percepciones']['Totalpercepcion']['TotalGravado'],
                                         'TotalExento': res['percepciones']['Totalpercepcion']['TotalExento'],
                                         'Percepcion': percepciones,
                                     },
                                     'Deducciones': {
                                         'Deduccion': res['deducciones']['lineas_de_deduccion'],
                                         'TotalImpuestosRetenidos': res['deducciones']['TotalDeduccion']['TotalImpuestosRetenidos'],
                                         'TotalOtrasDeducciones': res['deducciones']['TotalDeduccion']['TotalOtrasDeducciones'],
                                     },
                                 },
                             }
                             ]
                         },
                     }
                 }}
        
       
            else:
                nuevo_xml = {
                'localizacion-mx':
                 {
                     'Login': login,

                     'Documento': {
                         'Operacion': 'TIMBRAR',
                         'TipoDocumento': 'NOMINA',
                         'Comprobante': {
                             'Version': '3.3',
                             'Folio': res['factura']['folio'],
                             'Fecha': res['factura']['fecha_factura'].replace(' ', 'T'),
                             'Sello': '', 
                             'FormaPago': res['factura']['forma_pago'],
                             'NoCertificado': '',
                             'Certificado': '',
                             'CfdiRelacionados': {
                                 'CfdiRelacionado': {
                                     'UUID': '',  
                                 },
                                 'TipoRelacion': '',  
                             },
                             'Moneda': res['factura']['moneda'],
                             'TipoDeComprobante': res['factura']['tipocomprobante'],
                             'MetodoPago': res['factura']['metodo_pago'],
                             'Exportacion': '01',
                             'LugarExpedicion': res['factura']['LugarExpedicion'],
                             'SubTotal': res['factura']['subtotal'], 
                             'Descuento': res['factura']['descuento'], 
                             'Total': res['factura']['total'],
                             'Emisor': {
                                 'Rfc': emisor_rfc[2:len(emisor_rfc)-1],
                                 'Nombre': emisor_nombre[2:len(emisor_nombre)-1],
                                 'RegimenFiscal': res['factura']['RegimenFiscal'],
                             },
                             'Receptor': {
                                 'Rfc': receptor_rfc[2:len(receptor_rfc)-1],
                                 'Nombre': receptor_nombre[2:len(receptor_nombre)-1],
                                 'UsoCFDI': 'CN01',#res['receptor']['uso_cfdi'],
                                 'RegimenFiscalReceptor': '605',                    
                                 'DomicilioFiscalReceptor': self.employee_id.address_home_id.sat_codigopostal_id.code,#res['factura']['LugarExpedicion'],
                             },
                             'Complemento': {
                                 'TimbreFiscaldigital': {
                                     'TimbreFiscaldigital': '',  
                                     'FechaTimbrado': '',  
                                     'NoCertificadoSAT': '',  
                                     'RfcProvCertif': '',  
                                     'SelloCFD': '',  
                                     'SelloSAT': '',  
                                     'UUID': '',  
                                     'Version': '',  
                                 },
                                 'Pagos': {
                                     'Version': '',  
                                 },
                             },
                             'Conceptos': {
                                 'Concepto': 
                                 [
                                 {
                                     'ClaveProdServ': res['conceptos']['ClaveProdServ'],
                                     'NoIdentificacion': '',  
                                     'Cantidad': res['conceptos']['cantidad'],
                                     'ClaveUnidad': res['conceptos']['ClaveUnidad'],
                                     'Descripcion': concepto_dsc[2:len(concepto_dsc)-1],
                                     'ValorUnitario': res['conceptos']['valorunitario'], 
                                     'Importe': res['conceptos']['importe'],
                                     'Descuento': res['conceptos']['descuento'],
                                     'ObjetoImp': '01',
                                 }],
                             },
                             'Complementos': [
                             {
                                 'Nomina12': {
                                     'Version': '1.2',  
                                     'TipoNomina': res['nomina12']['TipoNomina'],
                                     'FechaPago': res['nomina12']['FechaPago'],
                                     'FechaInicialPago': res['nomina12']['FechaInicialPago'],
                                     'FechaFinalPago': res['nomina12']['FechaFinalPago'],
                                     'NumDiasPagados': res['nomina12']['NumDiasPagados'],
                                     'PeriodicidadPago': res['nomina12Receptor']['PeriodicidadPago'],
                                     'TotalPercepciones': res['nomina12']['TotalPercepciones'],
                                     'TotalDeducciones': res['nomina12']['TotalDeducciones'],
                                     'TotalOtrosPagos': res['nomina12']['TotalOtrosPagos'],
                                     'Receptor': {
                                         'Curp': curp_receptor[2:len(curp_receptor)-1],#res['nomina12Receptor']['Curp'], codificar
                                         'NumSeguridadSocial': res['nomina12Receptor']['NumSeguridadSocial'] or "",
                                         'FechaInicioRelLaboral': res['nomina12Receptor']['FechaInicioRelLaboral'],
                                         'Antiguedad': antiguedad_receptor[2:len(antiguedad_receptor)-1],#res['nomina12Receptor']['Antiguedad'], codificar
                                         'TipoContrato': res['nomina12Receptor']['TipoContrato'],
                                         'Sindicalizado': 'No',  
                                         'PeriodicidadPago': res['nomina12Receptor']['PeriodicidadPago'],
                                         'TipoJornada': res['nomina12Receptor']['TipoJornada'],
                                         'TipoRegimen': res['nomina12Receptor']['TipoRegimen'],
                                         'NumEmpleado': res['nomina12Receptor']['NumEmpleado'],
                                         'RiesgoPuesto': res['nomina12Receptor']['RiesgoPuesto'] or "",
                                         'Departamento': departmento_receptor[2:len(departmento_receptor)-1],#res['nomina12Receptor']['Departamento'], codificar
                                         'Puesto': puesto_receptor[2:len(puesto_receptor)-1],#res['nomina12Receptor']['Puesto'], codificar
                                         'SalarioBaseCotApor': res['nomina12Receptor']['SalarioBaseCotApor'],
                                         'SalarioDiarioIntegrado': res['nomina12Receptor']['SalarioDiarioIntegrado'],
                                         'ClaveEntFed': res['nomina12Receptor']['ClaveEntFed'],
                                     },
                                     'Emisor':{

                                            'RegistroPatronal': regritrop,#registropatronal[2:len(registropatronal)-1] or "",#res['nomina12Emisor']['RegistroPatronal'],
                                            'RfcPatronOrigen': rfpatron[2:len(rfpatron)-1],#res['nomina12Emisor']['RfcPatronOrigen'],
                                            #'Curp': curp_emisor[2:len(curp_emisor)-1] or '',
                                     },
                                    

                                      'OtrosPagos': { 
                                             'OtroPago': [
                                             {
                                                 'TipoOtroPago': res['otros_pagos']['otros_pagos'][0]['TipoOtrosPagos'],
                                                 'Clave': res['otros_pagos']['otros_pagos'][0]['Clave'],
                                                 'Concepto': res['otros_pagos']['otros_pagos'][0]['Concepto'],
                                                 'Importe': res['otros_pagos']['otros_pagos'][0]['ImporteExento'],
                                                 #'SubsidioAlEmpleo': {
                                                 #    'SubsidioCausado': self.subsidio_periodo,
                                                 #},
                                                  
                                             },
                                             {
                                              'TipoOtroPago': '002',
                                                 'Clave': 'O002',
                                                 'Concepto': concepto_dec,
                                                 'Importe': 0,
                                             'SubsidioAlEmpleo': {
                                                     'SubsidioCausado': 0,
                                              }   }
                                             ]},
                                     'Percepciones': {
                                         'TotalSueldos': res['percepciones']['Totalpercepcion']['TotalSueldos'],
                                         'TotalGravado': res['percepciones']['Totalpercepcion']['TotalGravado'],
                                         'TotalExento': res['percepciones']['Totalpercepcion']['TotalExento'],
                                         'Percepcion': percepciones,
                                     },
                                     'Deducciones': {
                                         'Deduccion': res['deducciones']['lineas_de_deduccion'],
                                         'TotalImpuestosRetenidos': res['deducciones']['TotalDeduccion']['TotalImpuestosRetenidos'],
                                         'TotalOtrasDeducciones': res['deducciones']['TotalDeduccion']['TotalOtrasDeducciones'],
                                     },
                                 },
                             }
                             ]
                         },
                     }
                 }}        
            
        else:
            _logger.info('nootrospagos')
            if self.tipo_relacion and self.uuid_relacionado:
                nuevo_xml = {
                'localizacion-mx':
                 {
                     'Login': login,

                     'Documento': {
                         'Operacion': 'TIMBRAR',
                         'TipoDocumento': 'NOMINA',
                         'Comprobante': {
                             'Version': '3.3',
                             'Folio': res['factura']['folio'],
                             'Fecha': res['factura']['fecha_factura'].replace(' ', 'T'),
                             'Sello': '', 
                             'FormaPago': res['factura']['forma_pago'],
                             'NoCertificado': '',
                             'Certificado': '',
                             'CfdiRelacionados': {
                                 'CfdiRelacionado': {
                                     'UUID': self.uuid_relacionado,  
                                 },
                                 'TipoRelacion': self.tipo_relacion,  
                             },
                             'Moneda': res['factura']['moneda'],
                             'TipoDeComprobante': res['factura']['tipocomprobante'],
                             'MetodoPago': res['factura']['metodo_pago'],
                             'Exportacion': '01',
                             'LugarExpedicion': res['factura']['LugarExpedicion'],
                             'SubTotal': res['factura']['subtotal'], 
                             'Descuento': res['factura']['descuento'], 
                             'Total': res['factura']['total'],
                             'Emisor': {
                                 'Rfc': emisor_rfc[2:len(emisor_rfc)-1],
                                 'Nombre': emisor_nombre[2:len(emisor_nombre)-1],
                                 'RegimenFiscal': res['factura']['RegimenFiscal'],
                             },
                             'Receptor': {
                                 'Rfc': receptor_rfc[2:len(receptor_rfc)-1],
                                 'Nombre': receptor_nombre[2:len(receptor_nombre)-1],
                                 'UsoCFDI': 'CN01',#res['receptor']['uso_cfdi'],
                                 'RegimenFiscalReceptor': '605',                    
                                 'DomicilioFiscalReceptor': self.employee_id.address_home_id.sat_codigopostal_id.code,#res['factura']['LugarExpedicion'],
                             },
                             'Complemento': {
                                 'TimbreFiscaldigital': {
                                     'TimbreFiscaldigital': '',  
                                     'FechaTimbrado': '',  
                                     'NoCertificadoSAT': '',  
                                     'RfcProvCertif': '',  
                                     'SelloCFD': '',  
                                     'SelloSAT': '',  
                                     'UUID': '',  
                                     'Version': '',  
                                 },
                                 'Pagos': {
                                     'Version': '',  
                                 },
                             },
                             'Conceptos': {
                                 'Concepto': 
                                    [
                                 {
                                     'ClaveProdServ': res['conceptos']['ClaveProdServ'],
                                     'NoIdentificacion': '',  
                                     'Cantidad': res['conceptos']['cantidad'],
                                     'ClaveUnidad': res['conceptos']['ClaveUnidad'],
                                     'Descripcion': concepto_dsc[2:len(concepto_dsc)-1],
                                     'ValorUnitario': res['conceptos']['valorunitario'], 
                                     'Importe': res['conceptos']['importe'],
                                     'Descuento': res['conceptos']['descuento'],
                                     'ObjetoImp': '01',
                                 }],
                             },
                             'Complementos': 
                             [
                             {
                                 'Nomina12': {
                                     'Version': '1.2',  
                                     'TipoNomina': res['nomina12']['TipoNomina'],
                                     'FechaPago': res['nomina12']['FechaPago'],
                                     'FechaInicialPago': res['nomina12']['FechaInicialPago'],
                                     'FechaFinalPago': res['nomina12']['FechaFinalPago'],
                                     'NumDiasPagados': res['nomina12']['NumDiasPagados'],
                                     'PeriodicidadPago': res['nomina12Receptor']['PeriodicidadPago'],
                                     'TotalPercepciones': res['nomina12']['TotalPercepciones'],
                                     'TotalDeducciones': res['nomina12']['TotalDeducciones'],
                                     'TotalOtrosPagos': res['nomina12']['TotalOtrosPagos'],
                                     'Receptor': {
                                         'Curp': curp_receptor[2:len(curp_receptor)-1],#res['nomina12Receptor']['Curp'], codificar
                                         'NumSeguridadSocial': res['nomina12Receptor']['NumSeguridadSocial'] or "",
                                         'FechaInicioRelLaboral': res['nomina12Receptor']['FechaInicioRelLaboral'],
                                         'Antiguedad': antiguedad_receptor[2:len(antiguedad_receptor)-1],#res['nomina12Receptor']['Antiguedad'], codificar
                                         'TipoContrato': res['nomina12Receptor']['TipoContrato'],
                                         'Sindicalizado': 'No',  
                                         'PeriodicidadPago': res['nomina12Receptor']['PeriodicidadPago'],
                                         'TipoJornada': res['nomina12Receptor']['TipoJornada'],
                                         'TipoRegimen': res['nomina12Receptor']['TipoRegimen'],
                                         'NumEmpleado': res['nomina12Receptor']['NumEmpleado'],
                                         'Departamento': departmento_receptor[2:len(departmento_receptor)-1],#res['nomina12Receptor']['Departamento'], codificar
                                         'Puesto': puesto_receptor[2:len(puesto_receptor)-1],#res['nomina12Receptor']['Puesto'], codificar
                                         'SalarioBaseCotApor': res['nomina12Receptor']['SalarioBaseCotApor'],
                                         'SalarioDiarioIntegrado': res['nomina12Receptor']['SalarioDiarioIntegrado'],
                                         'ClaveEntFed': res['nomina12Receptor']['ClaveEntFed'],
                                     },
                                     'Emisor':{

                                            'RegistroPatronal': registrop,#registropatronal[2:len(registropatronal)-1],#res['nomina12Emisor']['RegistroPatronal'],
                                            'RfcPatronOrigen': rfpatron[2:len(rfpatron)-1],#res['nomina12Emisor']['RfcPatronOrigen'],
                                            #'Curp': curp_emisor[2:len(curp_emisor)-1] or '',
                                     },

                                       'OtrosPagos': { 
                                             'OtroPago': {
                                                 'TipoOtroPago': '002',
                                                 'Clave': 'O002',
                                                 'Concepto': concepto_dec,
                                                 'Importe': 0,
                                             'SubsidioAlEmpleo': {
                                                     'SubsidioCausado': 0,
                                                 }
                                             }
                                         },
                                     'Percepciones': {
                                         'TotalSueldos': res['percepciones']['Totalpercepcion']['TotalSueldos'],
                                         'TotalGravado': res['percepciones']['Totalpercepcion']['TotalGravado'],
                                         'TotalExento': res['percepciones']['Totalpercepcion']['TotalExento'],
                                         'Percepcion': percepciones,
                                     },
                                     'Deducciones': {
                                         'Deduccion': res['deducciones']['lineas_de_deduccion'],
                                         'TotalImpuestosRetenidos': res['deducciones']['TotalDeduccion']['TotalImpuestosRetenidos'],
                                         'TotalOtrasDeducciones': res['deducciones']['TotalDeduccion']['TotalOtrasDeducciones'],
                                     }, 
                                 },
                             }
                             ]
                         },
                     }
                 }}
            else:
                nuevo_xml = {
                'localizacion-mx':
                 {
                     'Login': login,

                     'Documento': {
                         'Operacion': 'TIMBRAR',
                         'TipoDocumento': 'NOMINA',
                         'Comprobante': {
                             'Version': '3.3',
                             'Folio': res['factura']['folio'],
                             'Fecha': res['factura']['fecha_factura'].replace(' ', 'T'),
                             'Sello': '', 
                             'FormaPago': res['factura']['forma_pago'],
                             'NoCertificado': '',
                             'Certificado': '',
                             'CfdiRelacionados': {
                                 'CfdiRelacionado': {
                                     'UUID': '',  
                                 },
                                 'TipoRelacion': '',  
                             },
                             'Moneda': res['factura']['moneda'],
                             'TipoDeComprobante': res['factura']['tipocomprobante'],
                             'MetodoPago': res['factura']['metodo_pago'],
                             'Exportacion': '01',
                             'LugarExpedicion': res['factura']['LugarExpedicion'],
                             'SubTotal': res['factura']['subtotal'], 
                             'Descuento': res['factura']['descuento'], 
                             'Total': res['factura']['total'],
                             'Emisor': {
                                 'Rfc': emisor_rfc[2:len(emisor_rfc)-1],
                                 'Nombre': emisor_nombre[2:len(emisor_nombre)-1],
                                 'RegimenFiscal': res['factura']['RegimenFiscal'],
                             },
                             'Receptor': {
                                 'Rfc': receptor_rfc[2:len(receptor_rfc)-1],
                                 'Nombre': receptor_nombre[2:len(receptor_nombre)-1],
                                 'UsoCFDI': 'CN01',#res['receptor']['uso_cfdi'],
                                 'RegimenFiscalReceptor': '605',                    
                                 'DomicilioFiscalReceptor': self.employee_id.address_home_id.sat_codigopostal_id.code,#res['factura']['LugarExpedicion'],
                             },
                             'Complemento': {
                                 'TimbreFiscaldigital': {
                                     'TimbreFiscaldigital': '',  
                                     'FechaTimbrado': '',  
                                     'NoCertificadoSAT': '',  
                                     'RfcProvCertif': '',  
                                     'SelloCFD': '',  
                                     'SelloSAT': '',  
                                     'UUID': '',  
                                     'Version': '',  
                                 },
                                 'Pagos': {
                                     'Version': '',  
                                 },
                             },
                             'Conceptos': {
                                 'Concepto': 
                                    [
                                 {
                                     'ClaveProdServ': res['conceptos']['ClaveProdServ'],
                                     'NoIdentificacion': '',  
                                     'Cantidad': res['conceptos']['cantidad'],
                                     'ClaveUnidad': res['conceptos']['ClaveUnidad'],
                                     'Descripcion': concepto_dsc[2:len(concepto_dsc)-1],
                                     'ValorUnitario': res['conceptos']['valorunitario'], 
                                     'Importe': res['conceptos']['importe'],
                                     'Descuento': res['conceptos']['descuento'],
                                     'ObjetoImp': '01',
                                 }],
                             },
                             'Complementos': 
                             [
                             {
                                 'Nomina12': {
                                     'Version': '1.2',  
                                     'TipoNomina': res['nomina12']['TipoNomina'],
                                     'FechaPago': res['nomina12']['FechaPago'],
                                     'FechaInicialPago': res['nomina12']['FechaInicialPago'],
                                     'FechaFinalPago': res['nomina12']['FechaFinalPago'],
                                     'NumDiasPagados': res['nomina12']['NumDiasPagados'],
                                     'PeriodicidadPago': res['nomina12Receptor']['PeriodicidadPago'],
                                     'TotalPercepciones': res['nomina12']['TotalPercepciones'],
                                     'TotalDeducciones': res['nomina12']['TotalDeducciones'],
                                     'TotalOtrosPagos': res['nomina12']['TotalOtrosPagos'],
                                     'Receptor': {
                                         'Curp': curp_receptor[2:len(curp_receptor)-1],#res['nomina12Receptor']['Curp'], codificar
                                         'NumSeguridadSocial': res['nomina12Receptor']['NumSeguridadSocial'] or "",
                                         'FechaInicioRelLaboral': res['nomina12Receptor']['FechaInicioRelLaboral'],
                                         'Antiguedad': antiguedad_receptor[2:len(antiguedad_receptor)-1],#res['nomina12Receptor']['Antiguedad'], codificar
                                         'TipoContrato': res['nomina12Receptor']['TipoContrato'],
                                         'Sindicalizado': 'No',  
                                         'PeriodicidadPago': res['nomina12Receptor']['PeriodicidadPago'],
                                         'TipoJornada': res['nomina12Receptor']['TipoJornada'],
                                         'TipoRegimen': res['nomina12Receptor']['TipoRegimen'],
                                         'NumEmpleado': res['nomina12Receptor']['NumEmpleado'],
                                         'RiesgoPuesto': res['nomina12Receptor']['RiesgoPuesto'] or "",
                                         'Departamento': departmento_receptor[2:len(departmento_receptor)-1],#res['nomina12Receptor']['Departamento'], codificar
                                         'Puesto': puesto_receptor[2:len(puesto_receptor)-1],#res['nomina12Receptor']['Puesto'], codificar
                                         'SalarioBaseCotApor': res['nomina12Receptor']['SalarioBaseCotApor'],
                                         'SalarioDiarioIntegrado': res['nomina12Receptor']['SalarioDiarioIntegrado'],
                                         'ClaveEntFed': res['nomina12Receptor']['ClaveEntFed'],
                                     },
                                     'Emisor':{

                                            'RegistroPatronal': registrop, #registropatronal[2:len(registropatronal)-1],#res['nomina12Emisor']['RegistroPatronal'],
                                            'RfcPatronOrigen': rfpatron[2:len(rfpatron)-1],#res['nomina12Emisor']['RfcPatronOrigen'],
                                            #'Curp': curp_emisor[2:len(curp_emisor)-1] or '',
                                     },

                                       'OtrosPagos': { 
                                             'OtroPago': {
                                                 'TipoOtroPago': '002',
                                                 'Clave': 'O002',
                                                 'Concepto': concepto_dec,
                                                 'Importe': 0,
                                             'SubsidioAlEmpleo': {
                                                     'SubsidioCausado': 0,
                                                 }
                                             }
                                         },
                                     'Percepciones': {
                                         'TotalSueldos': res['percepciones']['Totalpercepcion']['TotalSueldos'],
                                         'TotalGravado': res['percepciones']['Totalpercepcion']['TotalGravado'],
                                         'TotalExento': res['percepciones']['Totalpercepcion']['TotalExento'],
                                         'Percepcion': percepciones,
                                     },
                                     'Deducciones': {
                                         'Deduccion': res['deducciones']['lineas_de_deduccion'],
                                         'TotalImpuestosRetenidos': res['deducciones']['TotalDeduccion']['TotalImpuestosRetenidos'],
                                         'TotalOtrasDeducciones': res['deducciones']['TotalDeduccion']['TotalOtrasDeducciones'],
                                     }, 
                                 },
                             }
                             ]
                         },
                     }
                 }}

        _logger.error('datos: %s', nuevo_xml)   
        """dir = '/home'
        filename = "nomina40.json"
        with open(os.path.join(dir, filename), 'w') as file:
            json.dump(nuevo_xml, file)"""
        datos_cod = str(nuevo_xml).encode('utf-8')
        base64_datos = base64.b64encode(datos_cod)
        cadena = ""
        cadena = base64_datos.decode("utf-8")
        cadena_data = cadena
        data = {

               "datos":cadena_data
                

               }

        
        _logger.error('data: %s', data)

        headers = {'content-type': 'application/json'}        
        resp = requests.post(str(url) + "/Timbrar/CFDI", data=json.dumps(data), headers=headers)
        respuesta = json.loads(resp.content.decode("utf-8"))
        _logger.error('respuesta: %s', respuesta)
        xml_recep = ""        
        cfdi = dict()
        if respuesta['Codigo'] == 1:
            self.estado_factura = 'factura_correcta'
            self.nomina_cfdi = True
            self.folio_fiscal = respuesta['Data']['Timbre']['FolioFsical']            
            self.fecha_factura = datetime.datetime.now()
            self.selo_digital_cdfi = respuesta['Data']['Timbre']['SelloEmisor']
            xml_recep = respuesta['Data']['Timbre']['Xml']


            cfdi['type_document'] = self.tipo_comprobante
            cfdi['fecha_timbrado'] = datetime.datetime.now()
            cfdi['cfdi_num_certificado'] = self.company_id.serial_number
            cfdi['cfdi_sello'] = respuesta['Data']['Timbre']['SelloEmisor']
            cfdi['cfdi_folio'] = respuesta['Data']['Timbre']['FolioFsical']
            cfdi['cfdi_cadena_original'] = respuesta['Data']['Timbre']['CadenaOriginal']
            cfdi['pac_timbrado'] = respuesta['Data']['Timbre']['CFDIPac']
            cfdi['sello'] = respuesta['Data']['Timbre']['SelloSAT']
            cfdi['certificado'] = respuesta['Data']['Timbre']['NoCertificado']
            cfdi['total_docto'] = self.total_nomina
            cfdi['name'] = self.number
            cfdi['rfc_emisor'] = self.company_id.rfc
            cfdi['rfc_receptor'] = self.employee_id.rfc
            cfdi['codigo_bm'] = self.qrcode_image
            cfdi['pac_timbrado'] = respuesta['Data']['Timbre']['CFDIPac']
            cfdi['currency_id'] = self.company_id.currency_id.id
            self.env['xmlcfdi'].create(cfdi)
            xml_dec = base64.decodestring(str.encode(xml_recep))            
            xml_dec= xml_dec.decode("utf-8").replace('\r\n','') 
            xml_file_name = self.number.replace('/','_') + '.xml'
            options = {'width': 275 * mm, 'height': 275 * mm}
            amount_str = str(self.total_nomina).split('.')
            #print 'amount_str, ', amount_str
            qr_value = 'https://verificacfdi.facturaelectronica.sat.gob.mx/default.aspx?&id=%s&re=%s&rr=%s&tt=%s.%s&fe=%s' % (self.folio_fiscal,
                                                     self.company_id.rfc,
                                                     self.employee_id.rfc,
                                                     amount_str[0].zfill(10),
                                                     amount_str[1].ljust(6, '0'),
                                                     self.selo_digital_cdfi[-8:],
                                                     )
            self.qr_value = qr_value
            ret_val = createBarcodeDrawing('QR', value=qr_value, **options)
            self.qrcode_image = base64.encodestring(ret_val.asString('jpg'))

            attachment_obj = self.env['ir.attachment']   

            
            data_at = {
                        'name': xml_file_name,
                        'datas': base64.encodestring(str.encode(xml_dec)),               
                        'description': 'Archivo XML del Comprobante Fiscal Digital de nomina',
                        'res_model': self._name,
                        'res_id': self.id,
                        'type': 'binary',                        
            }
            attach = attachment_obj.with_context({}).create(data_at)
            xres = self.do_something_with_xml_attachment(attach)
            
            report = self.env['ir.actions.report']._get_report_from_name('nomina_cfdi_ee.report_payslip')
            report_data = report._render_qweb_pdf([self.id])[0]
            pdf_file_name = self.number.replace('/','_') + '.pdf'
            self.env['ir.attachment'].sudo().create(
                                        {
                                            'name': pdf_file_name,
                                            'datas': base64.b64encode(report_data),                                           
                                            'res_model': self._name,
                                            'res_id': self.id,
                                            'type': 'binary'
                                        })
            """options = {'width': 275 * mm, 'height': 275 * mm}
            amount_str = str(self.total_nomina).split('.')
            #print 'amount_str, ', amount_str
            qr_value = 'https://verificacfdi.facturaelectronica.sat.gob.mx/default.aspx?&id=%s&re=%s&rr=%s&tt=%s.%s&fe=%s' % (self.folio_fiscal,
                                                     self.company_id.rfc, 
                                                     self.employee_id.rfc,
                                                     amount_str[0].zfill(10),
                                                     amount_str[1].ljust(6, '0'),
                                                     self.selo_digital_cdfi[-8:],
                                                     )
            self.qr_value = qr_value
            ret_val = createBarcodeDrawing('QR', value=qr_value, **options)
            self.qrcode_image = base64.encodestring(ret_val.asString('jpg'))"""
        else:            
            if respuesta['Codigo'] == 0:
                raise UserError(_("Error de Timbrado:\n\n %s" % respuesta['Data']['Error']['CodigoError'] +' '+ respuesta['Data']['Error']['DescripcionError']))
        return res

