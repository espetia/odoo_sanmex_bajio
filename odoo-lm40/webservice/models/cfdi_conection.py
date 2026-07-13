# -*- coding: utf-8 -*-

from odoo import models, fields, _, api
import requests
import json
import urllib
import base64
from odoo.exceptions import UserError, RedirectWarning, ValidationError
import logging
_logger = logging.getLogger(__name__)

class ResCompany(models.Model):
    _inherit = 'res.company'   
    URLS = [
      ('product', "Url WebService Produccion"),
      ('test', "Url WebService Test")]

    url = fields.Selection(URLS, "URL's WebService", default='test')
    url_name_produc = fields.Char('Url Producción')
    url_name_prue = fields.Char('Url Pruebas')     
    razon_social = fields.Char('Razon Social')
    rfc_web = fields.Char('RFC')
    deposit_product_id = fields.Many2one('product.product', 'Producto Anticipo', domain="[('type', '=', 'service')]")
    user = fields.Char('Usuario')
    password = fields.Char('Clave')
    taxes_id = fields.Many2one('account.tax', string='Impuestos para Estimulo', domain=[('type_tax_use', '=', 'sale')])
    producto_pago = fields.Many2one('product.product', string='Concepto complemento')
    rfc_web_1 = fields.Char('Usuario')
    password_1 = fields.Char('Clave')
    multi_company = fields.Boolean('Multi-compañia')






    #@api.model
    def registro_webservice(self):
        login = {}
        webservice_url = self.env['ir.config_parameter'].sudo().get_param('webservice.url')
        config_up =  self.env['ir.config_parameter'].search([('key','=','database.uuid')])
        multi_company = self.env['ir.config_parameter'].sudo().get_param('webservice.multi_company')
        """if multi_company == True:
           rfc_acceso = self.rfc_web_1
           password = self.password_1
        if multi_company == False:
           rfc_acceso = self.env['ir.config_parameter'].sudo().get_param('webservice.rfc_web')
           password = self.env['ir.config_parameter'].sudo().get_param('webservice.password')"""
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

        #rfc_acceso = self.env['ir.config_parameter'].sudo().get_param('webservice.rfc_web')
        if rfc_acceso != self.rfc:
           raise UserError(_("El RFC no coincide con el proporcionado en su contrato"))

        data = {}

        if self.pac_testing == False:
           if self.certificate_file and self.certificate_password and \
           self.pac_user and self.certificate_key_file and \
           self.pac_password and self.pac_equipo_id and self.url_productivo_pac and \
           self.url_cancelacion_pac_prodc:

               cer_64 = base64.b64encode(self.certificate_file)
               key_64 = base64.b64encode(self.certificate_key_file)
               pem_64 = base64.b64encode(self.certificate_file_pem)
               pem_key_64 = base64.b64encode(self.certificate_key_file_pem)
               cer_env = cer_64.decode("utf-8")
               key_env = key_64.decode("utf-8")
               pem_env = pem_64.decode("utf-8")
               pfx_env = self.certificate_pfx_file.decode("utf-8")
               pem_key_env = pem_key_64.decode("utf-8")

               data = {

                      "login":login,

                      "contrato":
                          {
                          "name": self.partner_id.name,
                          "regname": self.razonsocial,
                          "rfc": self.rfc,
                          "street": self.street or '',
                          "l10n_mx_street3": self.num_external or '',
                          "l10n_mx_street4": self.num_internal or '',
                          "Telefono": self.phone or '',
                          "zip_sat_id": self.codigopostal_sat_id.code,
                          "colonia_sat_id": self.colonia_sat_id. name or '',
                          "township_sat_id": self.sat_municipio_id.name or '',
                          "state_id": self.state_id.name or '',
                          "country_id": self.country_id.name or '',
                          "email": self.email or '',
                          "ContraseniaCertificado": self.certificate_password,
                          "BaseDatosUUID": config_up.value

                          },


                      "cfdi":
                     {
                        "SAT_ClaveLlave": self.certificate_password,
                        "SAT_NumeroSerie": self.serial_number,
                        "SAT_CertificadoB64": cer_env,
                        "SAT_CertificadoKeyB64": key_env,
                        "SAT_CertificadoPemB64": pem_env,
                        "SAT_CertificadoPFXB64": pfx_env,
                        "SAT_LLaveCertificadoPEMB64": pem_key_env,
                        #"SAT_Certificado_Vigencia_Desde": self.date_start,
                        #"SAT_Certificado_Vigencia_Hasta": self.date_end,
                        "PAC_Pruebas": 'true',
                        "PAC_Usuario": self.pac_user,
                        "PAC_Clave": self.pac_password,
                        "PAC_EquipoID": self.pac_equipo_id,
                        "PacID": self.cat_pacs.name,
                        "ConfiguracionID": self.config_webservice,
                        "PAC_URL": self.url_productivo_pac,
                        "CompaniaEmisora": self.razonsocial,
                        "PAC_URL_Cancelacion": self.url_cancelacion_pac_prodc
                      }
                }
           headers = {'content-type': 'application/json'}
           respuesta = requests.post(str(url) + "/contrato/registrar", data=json.dumps(data), headers=headers)
           resp = json.loads(respuesta.content.decode("utf-8"))
           _logger.error('Respuesta web: %s', resp)

           if resp['contrato']['cfdi']['ConfiguracionPacID'] > 0:

               config_webservice = resp['contrato']['cfdi']['ConfiguracionPacID']
               self._cr.execute("UPDATE res_company set config_webservice=%s where id=%s", (config_webservice, self.id))

           else:
               raise UserError(_("No se registraron sus datos:%s" % resp['contrato']['cfdi']['ConfiguracionPacID']))

        else:
           if self.certificate_file and self.certificate_password and \
           self.pac_user_4_testing and self.certificate_key_file and \
           self.pac_password_4_testing and self.pac_equipo_id_4_testing and self.url_pruebas_pac and \
           self.url_cancelacion_pac_prue:
               _logger.error("Fecha inicio: %s", self.date_start)
               cer_64 = base64.b64encode(self.certificate_file)
               key_64 = base64.b64encode(self.certificate_key_file)
               pem_64 = base64.b64encode(self.certificate_file_pem)
               pem_key_64 = base64.b64encode(self.certificate_key_file_pem)
               cer_env = cer_64.decode("utf-8")
               key_env = key_64.decode("utf-8")
               pem_env = pem_64.decode("utf-8")
               pfx_env = self.certificate_pfx_file.decode("utf-8")
               pem_key_env = pem_key_64.decode("utf-8")

               data = {

                        "login": login,

                        "contrato":
                          {
                          "name": self.partner_id.name,
                          "regname": self.razonsocial,
                          "rfc": self.rfc,
                          "street": self.street,
                          "l10n_mx_street3": self.num_external,
                          "l10n_mx_street4": self.num_internal,
                          "Telefono": self.phone,
                          "zip_sat_id": self.codigopostal_sat_id.code,
                          "colonia_sat_id": self.colonia_sat_id. name,
                          "township_sat_id": self.sat_municipio_id.name,
                          "state_id": self.state_id.name,
                          "country_id": self.country_id.name,
                          "email": self.email,
                          "ContraseniaCertificado": self.certificate_password,
                          "BaseDatosUUID": config_up.value

                          },

                        "cfdi":
                      {

                        "SAT_ClaveLlave": self.certificate_password,
                        "SAT_NumeroSerie": self.serial_number,
                        "SAT_CertificadoB64": cer_env,
                        "SAT_CertificadoKeyB64": key_env,
                        "SAT_CertificadoPemB64": pem_env,
                        "SAT_CertificadoPFXB64": pfx_env,
                        "SAT_LLaveCertificadoPEMB64": pem_key_env,
                        "SAT_Certificado_Vigencia_Desde": self.date_start,
                        "SAT_Certificado_Vigencia_Hasta": self.date_end,
                        "PAC_Pruebas": 'true',
                        "PAC_Usuario": self.pac_user_4_testing,
                        "PAC_Clave": self.pac_password_4_testing,
                        "PAC_EquipoID": self.pac_equipo_id_4_testing,
                        "PacID": self.cat_pacs.name,
                        "ConfiguracionID": self.config_webservice,
                        "PAC_URL": self.url_pruebas_pac,
                        "CompaniaEmisora": self.razonsocial,
                        "PAC_URL_Cancelacion": self.url_cancelacion_pac_prue
                      }
                  }

           _logger.error('Datos: %s', data)
           headers = {'content-type': 'application/json'}
           respuesta = requests.post(str(url) + "/contrato/registrar", data=json.dumps(data), headers=headers)
           resp = json.loads(respuesta.content.decode("utf-8"))
           _logger.error('Respuesta web: %s', resp)

           if resp['contrato']['cfdi']['ConfiguracionPacID'] > 0:

               config_webservice = resp['contrato']['cfdi']['ConfiguracionPacID']
               self._cr.execute("UPDATE res_company set config_webservice=%s where id=%s", (config_webservice, self.id))
           else:
               raise UserError(_("No se registraron sus datos:%s" % resp['contrato']['cfdi']['ConfiguracionPacID']))
             
         

class webserviceConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'
    URLS = [
      ('product', "Url WebService Produccion"),
      ('test', "Url WebService Test")]

    
    url = fields.Selection(URLS, "URL", default='test', config_parameter='webservice.url')    
    url_name_prue = fields.Char('Pruebas', config_parameter='webservice.url_name_prue')    
    url_name_produc = fields.Char('Producción', config_parameter='webservice.razon_social')     
    razon_social = fields.Char("Razon", config_parameter='webservice.razon_social')    
    rfc_web = fields.Char("RFC", config_parameter='webservice.rfc_web')   
    deposit_product_id = fields.Many2one('product.product', 'Deposit Product', domain="[('type', '=', 'service')]",
        config_parameter='webservice.deposit_product_id', readonly=False)
    user = fields.Char('Usuario', config_parameter='webservice.user')    
    password = fields.Char("Password", config_parameter='webservice.password')    
    taxes_id = fields.Many2one('account.tax', 'impuestos', config_parameter='webservice.taxes_id', readonly=False)    
    producto_pago = fields.Many2one('product.product', 'pago', config_parameter='webservice.producto_pago', readonly=False)
    multi_company = fields.Boolean('Multi-compañia', config_parameter='webservice.multi_company')


    
        
    @api.model
    def get_values(self):
        res = super(webserviceConfigSettings, self).get_values()
        ICPSudo = self.env['ir.config_parameter'].sudo()        
        res.update(
            url = ICPSudo.get_param('webservice.url', default=False),
            url_name_prue = ICPSudo.get_param('webservice.url_name_prue'),
            url_name_produc = ICPSudo.get_param('webservice.url_name_produc'),        
            razon_social = ICPSudo.get_param('webservice.razon_social'),
            rfc_web = ICPSudo.get_param('webservice.rfc_web'),            
            user = ICPSudo.get_param('webservice.user'),
            password = ICPSudo.get_param('webservice.password'),
            multi_company=ICPSudo.get_param('webservice.multi_company', default=False),
            #deposit_produc_id = ICPSudo.get_param("webservice.deposit_product_id.id"),
            #producto_pago = ICPSudo.get_param('webservice.producto_pago'),
        
        )
        return res

        
        

class historialactaulizaciones(models.Model):
    _name = "actua.historial"


    modelo_id = fields.Char('Modelo Actualizado', readonly=True)
    FechaLiberacion = fields.Datetime('Fecha de Liberación', readonly=True)
    Version_ws = fields.Char('Versión ws', readonly=True)
    Version_sat = fields.Char('Versión SAT', readonly=True)
    Actualizacion = fields.Datetime('Actualización', readonly=True)
    Creacion = fields.Datetime('Creación', readonly=True)
    Notas = fields.Text('Notas', readonly=True)
    
class registroactaulizaciones(models.Model):
    _name = "actua.registro"

    name = fields.Char("No. de Registro", default=lambda self: _('New'), readonly=True)
    modelo_id = fields.Char('Modelo Actualizado', readonly=True)   
    actualizacion = fields.Date('Ultima Actualización', readonly=True)
    creacion = fields.Datetime('Fecha de Creación', readonly=True)

    @api.model
    def create(self, vals):
        if vals.get('name', _('New')) == _('New'):
            if 'company_id' in vals:
                vals['name'] = self.env['ir.sequence'].with_context(force_company=vals['company_id']).next_by_code('registroactaulizaciones') or _('New')
            else:
                vals['name'] = self.env['ir.sequence'].next_by_code('registroactaulizaciones') or _('New')

        result = super(registroactaulizaciones, self).create(vals)
        return result

     


   

     
      
     
     
        

         
        
         

