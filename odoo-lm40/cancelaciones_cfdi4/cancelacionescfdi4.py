from odoo import api, fields, models, _, tools
from datetime import datetime
import time
from odoo import SUPERUSER_ID
import time
import dateutil
import dateutil.parser
from datetime import datetime, date, timedelta
from odoo.exceptions import UserError, RedirectWarning, ValidationError
import re
import requests
import json
import urllib
import traceback
import qrcode
import codecs
import os
import sys
import io
from pytz import timezone
import pytz
import base64
from odoo.tools import DEFAULT_SERVER_DATETIME_FORMAT, DEFAULT_SERVER_DATE_FORMAT
import logging
_logger = logging.getLogger(__name__)
#from . import amount_to_text_es_MX


class AccountInvoice(models.Model):    
    _inherit ='account.move'


    @api.onchange('uuid_sustituye', 'cancelaciones_id')
    def _onchange_sustitucion(self):  
        _logger.info('dominio')
        if self.cancelaciones_id.code == '01':
            _logger.info('dominio1')   
            return {'domain': {'uuid_sustituye': [('invoice_date','>=',self.date.today()), ('state','=','posted'), ('invoice_payment_state','!=','paid'), ('partner_id','=', self.partner_id.id), ('cancel_solicitud','=',False), ('TipoDeComprobante.code','=', self.TipoDeComprobante.code)]}}

    cancelaciones_id = fields.Many2one('cancelaciones.cfdinuevo', string='Motivo de Cancelación', copy=False)
    uuid_sustituye = fields.Many2one('account.move', string='Factura Sustituta', copy=False)

   
        
    def cancelar_timbre(self):
        login = {}
        fname_xml = self.name_invoice and self.name_invoice + '.xml' or '' 
        webservice_url = self.env['ir.config_parameter'].sudo().get_param('webservice.url')
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
        if self.cancel_solicitud:
            raise UserError(_("La Factura ya cuenta con una solictud de cancelación")) 
        if not self.cancelaciones_id:
            raise UserError(_("Debes seleccionar el motivo de cancelación")) 
        if self.cancelaciones_id.code == '01':
            if not self.uuid_sustituye:
                raise UserError(_("Debes seleccionar la Factura que sustituye el CFDI a cancelar")) 
        if self.cancelaciones_id.code != '01':
            data = {
                      "Login": login,
                      "FoliosUUID": {
                      "FolioUUID": [
                      {
                      "UUID": '|'+self.UUID +'|'+self.cancelaciones_id.code+'|'+'|'
                       
                      
                      }
                      ]
                      }
                      }
        else:
            data = {
                      "Login": login,
                      "FoliosUUID": {
                      "FolioUUID": [
                      {
                      "UUID": '|'+self.UUID +'|'+self.cancelaciones_id.code+'|'+self.uuid_sustituye.UUID+'|'
                      
                      }
                      ]
                      }
                      }
        _logger.error("Cancelación: %s", data)
        headers =  {'content-type': 'application/json','timeout':'500000'}
        Respuesta =  requests.post(str(url) + "/v2/cfdi/cancela", data=json.dumps(data), headers=headers)                
        consulta =  json.loads(Respuesta.content.decode("utf-8"))
        _logger.error('consultas: %s', consulta)
        ad = dict()
        xml_recep = ""

        if consulta['Codigo'] == 1: 
            ad['type_document'] = self.tipo_documento_id.name or self.tipo_documento_id_nc.name
            ad['fecha_timbrado'] = self.FechaTimbrado
            ad['cfdi_num_certificado'] = self.compañia_emisora_id.serial_number
            ad['cfdi_sello'] = self.sello
            ad['cfdi_folio'] = self.UUID
            ad['cfdi_cadena_original'] = self.cfdi_cadena_original
            ad['pac_timbrado'] = self.pac_timbre
            ad['sello'] = self.Sello
            ad['certificado'] = self.no_certificado
            ad['total_docto'] = self.amount_total
            ad['factura'] = self.id
            ad['rfc_emisor'] = self.compañia_emisora_id.rfc
            ad['rfc_receptor'] = self.partner_id.rfc           
            ad['fecha_cancelacion'] = consulta['Data']['Cancela']['Acuse']["fecha"]
            ad["rfemisior"] = consulta['Data']['Cancela']['Acuse']["RefEmisor"]
            ad["folio_cancelacion"] = consulta['Data']['Cancela']['Acuse']["FolioCancelacion"] 
            ad['codigo_solicitud'] = consulta['Data']['Cancela']['Acuse']["EstatusUUID"]  
            xml_recep = consulta['Data']['Cancela']['Acuse']["XmlBase64"]             
          
            result = self.env['cancelaciones'].create(ad)
            self.cfdi_fecha_cancelacion = consulta['Data']['Cancela']['Acuse']["fecha"]
            self.cancel_solicitud = result.id
            xml_dec = base64.decodestring(str.encode(xml_recep))            
            xml_dec= xml_dec.decode("utf-8").replace('\r\n','') 
            _logger.error('Xml: %s', xml_dec)
            attachment_obj = self.env['ir.attachment']   
          
            data_at = {
                      'name': fname_xml,
                      'datas': base64.encodestring(str.encode(xml_dec)),                        
                      #'datas_fname': fname_xml,
                      'description': 'Archivo XML del Acuse de solicitud de cancelación',
                      'res_model': 'cancelaciones',
                      'res_id': result.id,
                      'type': 'binary',                        
             }
            _logger.error('Adjunto: %s', data_at)
            attach = attachment_obj.with_context({}).create(data_at)

            xres = self.with_context(cancelacion = True).do_something_with_xml_attachment(attach)

          


class CancelacionesCFDI4(models.Model):
    _name = 'cancelaciones.cfdinuevo'

    code = fields.Char('Código')
    name = fields.Char('Descripción')


    @api.depends('namename', 'code')
    def name_get(self):
        result = []
        for rec in self:
            if rec.name and rec.code:
                name = '[ '+rec.code+' ]' + ' ' + rec.name
                result.append((rec.id, name))
        return result

    
    @api.model
    def name_search(self, name, args=None, operator='ilike', limit=100):
        args = args or []
        domain = []
        if name:
            domain = ['|', ('code', '=ilike', name + '%'), ('name', operator, name)]
            if operator in expression.NEGATIVE_TERM_OPERATORS:
                domain = ['&', '!'] + domain[1:]
        recs = self.search(domain + args, limit=limit)
        return recs.name_get() 

class account_payment(models.Model):
    _inherit = 'account.payment' 

    cancelaciones_id = fields.Many2one('cancelaciones.cfdinuevo', string='Motivo de Cancelación', copy=False)
    uuid_sustituye = fields.Many2one('account.payment', string='Pago Sustituto', copy=False, domain="[('payment_type', '=', 'inbound')]") 


    def cancel_pago(self):
        login = {}
        fname_payment = self.fname_payment and self.fname_payment + \
                            '.xml' or ''
        webservice_url = self.env['ir.config_parameter'].sudo().get_param('webservice.url')
        webservice_url = self.env['ir.config_parameter'].sudo().get_param('webservice.url')
        multi_company = self.env['ir.config_parameter'].sudo().get_param('webservice.multi_company')
        if multi_company == False:
           
            login = {
            "rfc": self.env['ir.config_parameter'].sudo().get_param('webservice.rfc_web'),
            "clave": self.env['ir.config_parameter'].sudo().get_param('webservice.password')
            }
        else:
          #_logger.info('condición aceptada')
            login = {
            "rfc": self.company_id.rfc_web_1,
            "clave": self.company_id.password_1
            }
        if webservice_url == 'test':
            url = self.env['ir.config_parameter'].sudo().get_param('webservice.url_name_prue')
        if webservice_url == 'product':
            url = self.env['ir.config_parameter'].sudo().get_param('webservice.url_name_produc')
        if not self.cancelaciones_id:
            raise UserError(_("Debes seleccionar el motivo de cancelación")) 
        if self.cancelaciones_id.code == '01':
            if not self.uuid_sustituye:
                raise UserError(_("Debes seleccionar la Factura que sustituye el CFDI a cancelar")) 
        if self.cancelaciones_id.code != '01':
            data = {
                      "Login": login,
                      "FoliosUUID": {
                      "FolioUUID": [
                      {
                      "UUID": '|'+self.UUID +'|'+self.cancelaciones_id.code+'|'+'|'
                      
                      }
                      ]
                      }
                      }
        else:
            data = {
                      "Login": login,
                      "FoliosUUID": {
                      "FolioUUID": [
                      {
                      "UUID": '|'+self.UUID +'|'+self.cancelaciones_id.code+'|'+self.uuid_sustituye.UUID+'|'
                      
                      }
                      ]
                      }
                      }
        _logger.error("Cancelación: %s", data)
        headers =  {'content-type': 'application/json','timeout':'500000'}
        Respuesta =  requests.post(str(url) + "/v2/cfdi/cancela", data=json.dumps(data), headers=headers)                
        consulta =  json.loads(Respuesta.content.decode("utf-8"))
        _logger.error('consultas: %s', consulta)
        ad = dict()
        xml_recep = ""

        if consulta['Codigo'] == 1: 
            ad['type_document'] = "Pago"
            ad['fecha_timbrado'] = self.fecha_timbrado
            ad['cfdi_num_certificado'] = self.company_emitter_id.serial_number
            ad['cfdi_sello'] = self.cfdi_sello
            ad['cfdi_folio'] = self.UUID
            ad['cfdi_cadena_original'] = self.cfdi_cadena_original
            ad['pac_timbrado'] = self.pac_timbre
            ad['sello'] = self.sello
            ad['certificado'] = self.no_certificado
            ad['total_docto'] = self.amount
            ad['payment_id'] = self.id
            ad['rfc_emisor'] = self.company_emitter_id.rfc
            ad['rfc_receptor'] = self.partner_id.rfc           
            ad['fecha_cancelacion'] = consulta['Data']['Cancela']['Acuse']["fecha"]
            ad["rfemisior"] = consulta['Data']['Cancela']['Acuse']["RefEmisor"]
            ad["folio_cancelacion"] = consulta['Data']['Cancela']['Acuse']["FolioCancelacion"] 
            ad['codigo_solicitud'] = consulta['Data']['Cancela']['Acuse']["EstatusUUID"]  
            xml_recep = consulta['Data']['Cancela']['Acuse']["XmlBase64"]             
          
            result = self.env['cancelaciones'].create(ad)
            self.cfdi_fecha_cancelacion = consulta['Data']['Cancela']['Acuse']["fecha"]
            self.cancel_solicitud = result.id
            xml_dec = base64.decodestring(str.encode(xml_recep))            
            xml_dec= xml_dec.decode("utf-8").replace('\r\n','') 
          #_logger.error('Xml: %s', xml_dec)
            attachment_obj = self.env['ir.attachment']   
          
            data_at = {
                      'name': fname_payment,
                      'datas': base64.encodestring(str.encode(xml_dec)),                        
                      #'datas_fname': fname_payment,
                      'description': 'Archivo XML del Acuse de solicitud de cancelación',
                      'res_model': 'cancelaciones',
                      'res_id': result.id,
                      'type': 'binary',                        
            }
          #_logger.error('Adjunto: %s', data_at)
            attach = attachment_obj.with_context({}).create(data_at)

            xres = self.with_context(cancelacion = True).do_something_with_xml_attachment(attach)       
        return True