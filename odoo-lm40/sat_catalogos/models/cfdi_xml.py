# -*- encoding: utf-8 -*-

from odoo import api, fields, models, _, tools

from odoo.exceptions import UserError, RedirectWarning, ValidationError
from odoo.osv import osv, expression
import requests
import json
import urllib
import base64
import logging
_logger = logging.getLogger(__name__)


class xmlcdfi(models.Model):
    _name = "xmlcfdi"

    name = fields.Char("Folio de Factura", readonly=True)
    type_document = fields.Char("Tipo de Documento", readonly=True)
    fecha_timbrado = fields.Datetime('Fecha de Timbrado', readonly=True, store=True)
    cfdi_num_certificado = fields.Char('No. de Certificado Emisor', readonly=True)
    cfdi_sello = fields.Text('Sello Digital Emisor', readonly=True)
    cfdi_folio = fields.Char('UUID', readonly=True)
    cfdi_cadena_original = fields.Text('Cadena Original', readonly=True)
    pac_timbrado = fields.Char(string="Pac de Timbrado", readonly=True)    
    sello = fields.Text('Sello Digital SAT', readonly=True)
    certificado = fields.Text('Certificado SAT', readonly=True)    
    codigo_bm = fields.Binary('Código Bidimencional', readonly=True)
    total_docto = fields.Monetary('Total Factura', readonly=True)
    status_cfdi = fields.Char('Estatus CFDI', readonly=True)
    Es_cancelable = fields.Char('Es cancelable', readonly=True)
    status_cancelacion = fields.Char('Estatus Cancelación', readonly=True)
    rfc_emisor = fields.Char('RFC Emisior', readonly=True)
    rfc_receptor = fields.Char('RFC Receptor', readonly=True)
    codigo_status = fields.Char('Código Estatus', readonly=True)
    currency_id = fields.Many2one('res.currency', required=False, readonly=True,
        default=lambda self: self.env.user.company_id.currency_id.id)

    #@api.model
    def consulta_estatus_cfdi(self):
        webservice_url = self.env['ir.config_parameter'].sudo().get_param('webservice.url')
        if webservice_url == 'test':
            url = self.env['ir.config_parameter'].sudo().get_param('webservice.url_name_prue')
        if webservice_url == 'product':
            url = self.env['ir.config_parameter'].sudo().get_param('webservice.url_name_produc')
        if self.type_document == 'Pago':
            data = {
                      "uuid": self.cfdi_folio,
                      "receptor": self.rfc_receptor,
                      "emisor": self.rfc_emisor,
                      "total": 0    

                    }
        if self.type_document == 'Factura de Venta' or self.type_document == 'Factura de Anticipo' or self.type_document == 'Nota de Crédito (Bonificación/Devolución)' or self.type_document == 'Nota de Crédito (para aplicación de Anticipo)':
            data = {
                      "uuid": self.cfdi_folio,
                      "receptor": self.rfc_receptor,
                      "emisor": self.rfc_emisor,
                      "total": self.total_docto    

                    }
       
        _logger.error('data_enviada: %s', data)
        headers =  {'content-type': 'application/json','timeout':'500000'}
        Respuesta =  requests.post(str(url) + "/Consulta/Estado", data=json.dumps(data), headers=headers)                
        consulta =  json.loads(Respuesta.content.decode("utf-8"))
        _logger.error('consultas: %s', consulta)
        ad = dict()
        
        ad["status_cfdi"] = consulta["Estado"]
        ad["Es_cancelable"] = consulta["EsCancelable"]
        ad["status_cancelacion"] = consulta["EstatusCancelacion"]
        ad["codigo_status"] = consulta["CodigoEstatus"]
        invoice = self.env['account.move'].search([('name','=',self.name)])
        _logger.error('Datos: %s', ad)
        self.write(ad)
        
        """if self.status_cancelacion != "":
            self.state = 'done'
        else:
            self.state = 'draft'"""
        return True
    
    
    

    

    

        
class cancelacionCFDI(models.Model):
    _name = "cancelaciones"
    _inherit = ['mail.thread', 'mail.activity.mixin', 'portal.mixin']
    ESTADOS = [
        ('draft', "En Proceso"),
        ('done', "Terminada")]

    name = fields.Char("No. de Solicitud", default=lambda self: _('New'), readonly=True)
    factura = fields.Many2one("account.move", string="Folio", readonly=True)
    payment_id = fields.Many2one('account.payment', string="Numero de pago", readonly=True)
    type_document = fields.Char("Tipo de Documento", readonly=True)
    fecha_timbrado = fields.Datetime('Fecha de Timbrado', readonly=True)
    cfdi_num_certificado = fields.Char('No. de Certificado Emisor', readonly=True)
    cfdi_sello = fields.Text('Sello Digital Emisor', readonly=True)
    cfdi_folio = fields.Char('UUID', readonly=True)
    cfdi_cadena_original = fields.Text('Cadena Original', readonly=True)
    pac_timbrado = fields.Char(string="Pac de Timbrado", readonly=True)
    sello = fields.Text('Sello Digital SAT', readonly=True)
    certificado = fields.Text('Certificado SAT', readonly=True)    
    codigo_bm = fields.Binary('Código Bidimencional', readonly=True)
    total_docto = fields.Monetary('Total Factura', readonly=True)
    status_cfdi = fields.Char('Estatus CFDI', readonly=True)
    Es_cancelable = fields.Char('Es cancelable', readonly=True)
    status_cancelacion = fields.Char('Estatus Cancelación', readonly=True)
    rfc_emisor = fields.Char('RFC Emisior', readonly=True)
    rfc_receptor = fields.Char('RFC Receptor', readonly=True)
    codigo_status = fields.Char('Código Estatus', readonly=True)
    currency_id = fields.Many2one('res.currency', required=False, readonly=True,
        default=lambda self: self.env.user.company_id.currency_id.id)
    fecha_cancelacion = fields.Datetime('Fecha de Cancelación', readonly=True)
    rfemisior = fields.Char('RFC Emisor', readonly=True)
    folio_cancelacion = fields.Char('Folio de Cancelación', readonly=True)
    state = fields.Selection(ESTADOS, string="Estado", default='draft')    
    codigo_solicitud = fields.Char("Codigo Estatus UUID", readonly=True)
    cancel_appply = fields.Boolean(related="factura.cancel_appply", string="Aplicada", readonly=True)

    @api.model
    def create(self, vals):
        if vals.get('name', _('New')) == _('New'):
            if 'company_id' in vals:
                vals['name'] = self.env['ir.sequence'].with_context(force_company=vals['company_id']).next_by_code('cancelaciones') or _('New')
            else:
                vals['name'] = self.env['ir.sequence'].next_by_code('cancelaciones') or _('New')

        result = super(cancelacionCFDI, self).create(vals)
        return result

    #@api.model
    def consulta_estatus(self):
        data = {}
        webservice_url = self.env['ir.config_parameter'].sudo().get_param('webservice.url')
        if webservice_url == 'test':
            url = self.env['ir.config_parameter'].sudo().get_param('webservice.url_name_prue')
        if webservice_url == 'product':
            url = self.env['ir.config_parameter'].sudo().get_param('webservice.url_name_produc')
        if self.type_document == 'Pago':
            data = {
                      "uuid": self.cfdi_folio,
                      "receptor": self.rfc_receptor,
                      "emisor": self.rfc_emisor,
                      "total": 0   

                    }
        if self.type_document == 'Factura de Venta' or self.type_document == 'Factura de Anticipo' or self.type_document == 'Nota de Crédito (Bonificación/Devolución)' or self.type_document == 'Nota de Crédito (para aplicación de Anticipo)':
            data = {
                      "uuid": self.cfdi_folio,
                      "receptor": self.rfc_receptor,
                      "emisor": self.rfc_emisor,
                      "total": self.total_docto    

                    }
        

        _logger.error('data_enviada: %s', data)
        headers =  {'content-type': 'application/json','timeout':'500000'}
        Respuesta =  requests.post(str(url) + "/Consulta/Estado", data=json.dumps(data), headers=headers)                
        consulta =  json.loads(Respuesta.content.decode("utf-8"))
        _logger.error('consultas: %s', consulta)
        ad = dict()
        
        ad["status_cfdi"] = consulta["Estado"]
        ad["Es_cancelable"] = consulta["EsCancelable"]
        ad["status_cancelacion"] = consulta["EstatusCancelacion"]
        ad["codigo_status"] = consulta["CodigoEstatus"]
        invoice = self.factura
        pay = self.payment_id
        _logger.error('Datos: %s', ad)
        self.write(ad)
        
        if invoice:
            invoice.status_cancel = self.status_cfdi
        if pay:
            pay.status_cfdi = self.status_cfdi
        if self.status_cancelacion != "":
            self.state = 'done'
        else:
            self.state = 'draft'
        return True
    
    
        
    def consultacfdi(self, cron=False):
        data = {}
        webservice_url = self.env['ir.config_parameter'].sudo().get_param('webservice.url')
        if webservice_url == 'test':
            url = self.env['ir.config_parameter'].sudo().get_param('webservice.url_name_prue')
        if webservice_url == 'product':
            url = self.env['ir.config_parameter'].sudo().get_param('webservice.url_name_produc')
        cancelacion = self.env['cancelaciones'].search([('state','=','draft')])
        
        for can in cancelacion:
            if can.type_document == 'Pago':
                data = {
                      "uuid": can.cfdi_folio,
                      "receptor": can.rfc_receptor,
                      "emisor": can.rfc_emisor,
                      "total": 0   

                    }
            if can.type_document == 'Factura de Venta' or can.type_document == 'Factura de Anticipo' or can.type_document == 'Nota de Crédito (Bonificación/Devolución)' or can.type_document == 'Nota de Crédito (para aplicación de Anticipo)':
                data = {
                      "uuid": can.cfdi_folio,
                      "receptor": can.rfc_receptor,
                      "emisor": can.rfc_emisor,
                      "total": can.total_docto    

                    }    
            
                _logger.error('data_enviada: %s', data)    
        
           
            _logger.error('data_enviada: %s', data)
            headers =  {'content-type': 'application/json','timeout':'500000'}
            Respuesta =  requests.post(str(url) + "/Consulta/Estado", data=json.dumps(data), headers=headers)                
            consulta =  json.loads(Respuesta.content.decode("utf-8"))
            _logger.error('consultas: %s', consulta)
            ad = dict()
            
            ad["status_cfdi"] = consulta["Estado"]
            ad["Es_cancelable"] = consulta["EsCancelable"]
            ad["status_cancelacion"] = consulta["EstatusCancelacion"]
            ad["codigo_status"] = consulta["CodigoEstatus"]
            invoice = can.factura    
            pay = can.payment_id                
            _logger.error('Datos: %s', ad)
            can.write(ad)
            if can.type_document == 'Pago':
                pay.status_cfdi = can.status_cfdi
            if can.type_document == 'Factura de Venta' or can.type_document == 'Factura de Anticipo' or can.type_document == 'Nota de Crédito (Bonificación/Devolución)' or can.type_document == 'Nota de Crédito (para aplicación de Anticipo)': 
                invoice.status_cancel = can.status_cfdi
            if can.status_cancelacion != "":
                can.state = 'done'
            else:
                can.state = 'draft'

        return True
    


    