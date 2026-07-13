# -*- encoding: utf-8 -*-

from odoo import api, fields, models, _
import requests
import json
import urllib
import logging
_logger = logging.getLogger(__name__)
from odoo.exceptions import UserError, RedirectWarning, ValidationError
#from . import update_mx_data
from odoo.tools import DEFAULT_SERVER_DATETIME_FORMAT, DEFAULT_SERVER_DATE_FORMAT
from odoo.tools.misc import DEFAULT_SERVER_DATE_FORMAT, format_date
import datetime
from datetime import timedelta, datetime
import math
import time
import datetime
#import date

class overall_config_wizard_sat_models_cfdi(models.TransientModel):
    _inherit = 'overall.config.wizard.sat.models.cfdi'
    
    
    sat_cp = fields.Boolean('Todos')    
    c_ClaveTipoCarga = fields.Boolean('Tipo de carga')        
    c_ConfigMaritima = fields.Boolean('Configuración marítima')    
    c_CveTransporte = fields.Boolean('Clave del transporte')
    c_TipoEstacion = fields.Boolean('Tipo de estación')
    c_Estaciones = fields.Boolean('Puertos marítimos, Estaciones aeroportuarias y Estaciones férreas')
    c_ClaveUnidadPeso = fields.Boolean('Unidades de medida y Embalaje')
    c_MaterialPeligroso = fields.Boolean('Materiales Peligrosos')
    c_TipoEmbalaje = fields.Boolean('Tipo de Embalaje')    
    c_TipoPermiso = fields.Boolean('Tipo de Permiso')
    c_ParteTransporte = fields.Boolean('Partes del transporte rentadas o prestadas')
    c_FiguraTransporte = fields.Boolean('Figura de Transporte')
    c_ConfigAutoTransporte = fields.Boolean('Configuración autotransporte federal')    
    c_SubTipoRem = fields.Boolean('Tipo de remolque')    
    c_ContenedorMaritimo = fields.Boolean('Contenedores marítimos')
    c_NumAutorizacionNaviero = fields.Boolean('Número autorización agente naviero consignatario')
    c_CodigoTransporteAereo = fields.Boolean('Código transporte aéreo')
    c_TipoDeServicio = fields.Boolean('Tipo servicio')
    c_DerechosDePaso = fields.Boolean('Derechos de paso')
    c_TipoCarro = fields.Boolean('Tipo de carro')
    c_Contenedor = fields.Boolean('Contenedor')
    c_TipoDeTrafico = fields.Boolean('Tipo de tráfico ferroviario')     
    

       
    def carga_catalogos(self, Desde=0, Cuantos=0):
        res = super(overall_config_wizard_sat_models_cfdi, self).carga_catalogos()
        webservice_url = self.env['ir.config_parameter'].sudo().get_param('webservice.url')
        _logger.error("webserv: %s", webservice_url)
        rfc = self.env['ir.config_parameter'].sudo().get_param('webservice.rfc_web')
        clave = self.env['ir.config_parameter'].sudo().get_param('webservice.password')
        if webservice_url == 'test':
            url = self.env['ir.config_parameter'].sudo().get_param('webservice.url_name_prue')
        if webservice_url == 'product':
            url = self.env['ir.config_parameter'].sudo().get_param('webservice.url_name_produc')
        if not rfc or not clave or not url: 
            raise UserError(_("Error!\nlos Datos de conexión al webservice son incorrectos o estan vacios .\n\n" 'RFC: %s\n' 'Clave: %s\n' 'URL: %s\n') % (rfc, clave, url))          
                
        if self.c_ClaveTipoCarga == True:            
            data = {
                                    
                            "localizacion-mx":
                     { 
                     "Login":
                     { "rfc":rfc, "clave":clave
                     }, "Consulta":{ "Filtros":{ "fechadesde":"", "rangoinicial":"", "rangofinal":"", "paginar":"" }  } } } 
                         
            _logger.error('data: %s ', data)
            headers =  {'content-type': 'application/json','timeout':'500000'}
            Respuesta =  requests.post(str(url) + "/c_ClaveTipoCarga", data=json.dumps(data), headers=headers)                
            c_ClaveTipoCarga =  json.loads(Respuesta.content.decode("utf-8"))
            reg = dict()            
            for ClaveTipoCarga in c_ClaveTipoCarga:                                         
                self.env['c_clavetipocarga'].create(ClaveTipoCarga)
                _logger.info('\n******Fichero Cargado********\n')
            reg['modelo_id'] = 'Clave tipo carga'
            reg['actualizacion'] = fields.date.today()
            reg['creacion'] = fields.datetime.now()
            self.env['actua.registro'].create(reg)        
        

        if self.c_ConfigMaritima == True:
            
            data = {
                                    
                            "localizacion-mx":
                     { 
                     "Login":
                     { "rfc":rfc, "clave":clave
                     }, "Consulta":{ "Filtros":{ "fechadesde":"", "rangoinicial":"", "rangofinal":"", "paginar":"" } }} }
                       
            _logger.error('data: %s ', data)
            headers =  {'content-type': 'application/json','timeout':'500000'}
            Respuesta =  requests.post(str(url) + "/c_ConfigMaritima", data=json.dumps(data), headers=headers)
            res =  json.loads(Respuesta.content.decode("utf-8"))                  
            _logger.error('data: %s ', res)
            reg = dict()          
            for c_ConfigMaritima in res:                                                           
                self.env['configura.maritima'].create(c_ConfigMaritima)
                _logger.info('\n******Fichero Cargado********\n')
            reg['modelo_id'] = 'Configuración marítima'
            reg['actualizacion'] = fields.date.today()
            reg['creacion'] = fields.datetime.now()
            self.env['actua.registro'].create(reg)        
        
        if self.c_CveTransporte == True:
            
            data = {
                                    
                            "localizacion-mx":
                     { 
                     "Login":
                     { "rfc":rfc, "clave":clave
                     }, "Consulta":{ "Filtros":{ "fechadesde":"", "rangoinicial":"", "rangofinal":"", "paginar":"" } }} }
            
            headers =  {'content-type': 'application/json','timeout':'500000'}
            Respuesta =  requests.post(str(url) + "/c_CveTransporte", data=json.dumps(data), headers=headers)
            _logger.error('respuesta: %s', Respuesta)
            res =  json.loads(Respuesta.content.decode("utf-8"))
            _logger.error('respuesta: %s', res)             
            reg = dict()
            ad = dict()
            for c_CveTransporte in res:
                """ad['ClaveTransporte'] = c_CveTransporte['ClaveTransporte']
                ad['Descripcion'] = c_CveTransporte['Descripcion']
                ad['FechaInicioVigencia'] = c_CveTransporte['FechaInicioVigencia']"""                                                         
                self.env['c_cvetransporte'].create(c_CveTransporte)
                _logger.info('\n******Fichero Cargado********\n')
            reg['modelo_id'] = 'Clave Transporte'
            reg['actualizacion'] = fields.date.today()
            reg['creacion'] = fields.datetime.now()
            self.env['actua.registro'].create(reg)
        
        if self.c_TipoEstacion == True:
            
            data = {
                                    
                            "localizacion-mx":
                     { 
                     "Login":
                     { "rfc":rfc, "clave":clave
                     }, "Consulta":{ "Filtros":{ "fechadesde":"", "rangoinicial":"", "rangofinal":"", "paginar":"" } }} } 
                         
            headers =  {'content-type': 'application/json','timeout':'500000'}
            Respuesta =  requests.post(str(url) + "/c_TipoEstacion", data=json.dumps(data), headers=headers)
            res =  json.loads(Respuesta.content.decode("utf-8"))                 
            reg = dict()
            for c_TipoEstacion in res: 
                                                        
                self.env['c_tipoestacion'].create(c_TipoEstacion)
                _logger.info('\n******Fichero Cargado********\n')
            reg['modelo_id'] = 'Tipo Estación'
            reg['actualizacion'] = fields.date.today()
            reg['creacion'] = fields.datetime.now()
            self.env['actua.registro'].create(reg)
       

        if self.c_Estaciones == True:
            
            data = {
                                    
                            "localizacion-mx":
                     { 
                     "Login":
                     { "rfc":rfc, "clave":clave
                     }, "Consulta":{ "Filtros":{ "fechadesde":"", "rangoinicial":"", "rangofinal":"", "paginar":"" } }} }
                         
            headers =  {'content-type': 'application/json','timeout':'500000'}
            Respuesta =  requests.post(str(url) + "/c_Estaciones", data=json.dumps(data), headers=headers)
            res =  json.loads(Respuesta.content.decode("utf-8"))                  
            reg = dict()
            for c_Estaciones in res: 
                                                         
                self.env['c_estaciones'].create(c_Estaciones)
                _logger.info('\n******Fichero Cargado********\n')
            reg['modelo_id'] = 'Estaciones'
            reg['actualizacion'] = fields.date.today()
            reg['creacion'] = fields.datetime.now()
            self.env['actua.registro'].create(reg)

        if self.c_ClaveUnidadPeso == True:
            
            data = {
                                    
                            "localizacion-mx":
                     { 
                     "Login":
                     { "rfc":rfc, "clave":clave
                     }, "Consulta":{ "Filtros":{ "fechadesde":"", "rangoinicial":"", "rangofinal":"", "paginar":"" } } } } 
                         
            headers = {'content-type': 'application/json','timeout':'500000'}
            Respuesta =  requests.post(str(url) + "/c_ClaveUnidadPeso", data=json.dumps(data), headers=headers)
            res =  json.loads(Respuesta.content.decode("utf-8"))                   
            reg = dict()
            for c_ClaveUnidadPeso in res:                                          
                self.env['c_claveunidadpeso'].create(c_ClaveUnidadPeso)
                _logger.info('\n******Fichero Cargado********\n')
            reg['modelo_id'] = 'Clave Unidad de Peso'
            reg['actualizacion'] = fields.date.today()
            reg['creacion'] = fields.datetime.now()
            self.env['actua.registro'].create(reg)

        if self.c_MaterialPeligroso == True:
            
            data = {
                                    
                            "localizacion-mx":
                     { 
                     "Login":
                     { "rfc":rfc, "clave":clave
                     }, "Consulta":{ "Filtros":{ "fechadesde":"", "rangoinicial":"", "rangofinal":"", "paginar":"" } }} } 
                                          
                   
            headers =  {'content-type': 'application/json','timeout':'500000'}
            Respuesta =  requests.post(str(url) + "/c_MaterialPeligroso", data=json.dumps(data), headers=headers)
            res =  json.loads(Respuesta.content.decode("utf-8")) 
            _logger.error('res: %s', res)                 
            reg = dict()
            for c_MaterialPeligroso in res: 
                                                             
                self.env['c_materialpeligroso'].create(c_MaterialPeligroso)
                _logger.info('\n******Fichero Cargado********\n')
            reg['modelo_id'] = 'Materiale peligrosos'
            reg['actualizacion'] = fields.date.today()
            reg['creacion'] = fields.datetime.now()
            self.env['actua.registro'].create(reg)

        if self.c_TipoEmbalaje == True:            

            data = {
                                    
                            "localizacion-mx":
                     { 
                     "Login":
                     { "rfc":rfc, "clave":clave
                     }, "Consulta":{ "Filtros":{ "fechadesde":"", "rangoinicial":"", "rangofinal":"", "paginar":"" } } } } 
                        
            headers =  {'content-type': 'application/json','timeout':'500000'}
            Respuesta =  requests.post(str(url) + "/c_TipoEmbalaje", data=json.dumps(data), headers=headers)
            res =  json.loads(Respuesta.content.decode("utf-8"))        
            reg = dict()  
            for c_TipoEmbalaje in res:                                   
                self.env['c_tipoembalaje'].create(c_TipoEmbalaje)
                _logger.info('\n******Fichero Cargado********\n')
            reg['modelo_id'] = 'Tipo de embalaje'
            reg['actualizacion'] = fields.date.today()
            reg['creacion'] = fields.datetime.now()
            self.env['actua.registro'].create(reg)

        if self.c_TipoPermiso == True:
            
            data = {
                                    
                            "localizacion-mx":
                     { 
                     "Login":
                     { "rfc":rfc, "clave":clave
                     }, "Consulta":{ "Filtros":{ "fechadesde":"", "rangoinicial":"", "rangofinal":"", "paginar":"" } } } } 
                         
            headers =  {'content-type': 'application/json','timeout':'500000'}
            Respuesta =  requests.post(str(url) + "/c_TipoPermiso", data=json.dumps(data), headers=headers)
            res =  json.loads(Respuesta.content.decode("utf-8"))
            _logger.error('res: %s', res)   
                         
            reg = dict()
            for c_TipoPermiso in res:                                                                     
                self.env['c_tipopermiso'].create(c_TipoPermiso)
                _logger.info('\n******Fichero Cargado********\n')

            reg['modelo_id'] = 'Tipo de permiso'
            reg['actualizacion'] = fields.date.today()
            reg['creacion'] = fields.datetime.now()
            self.env['actua.registro'].create(reg)

        if self.c_ParteTransporte == True:
            
            data = {
                                    
                            "localizacion-mx":
                     { 
                     "Login":
                     { "rfc":rfc, "clave":clave
                     }, "Consulta":{ "Filtros":{ "fechadesde":"", "rangoinicial":"", "rangofinal":"", "paginar":"" } } } } 
                        
            headers =  {'content-type': 'application/json','timeout':'500000'}
            Respuesta =  requests.post(str(url) + "/c_ParteTransporte", data=json.dumps(data), headers=headers)
            res =  json.loads(Respuesta.content.decode("utf-8"))   
            _logger.error('res: %s', res)            
            reg = dict()            
            for c_ParteTransporte in res:                                                                                    
                self.env['c_partetransporte'].create(c_ParteTransporte)
                _logger.info('\n******Fichero Cargado********\n')
            reg['modelo_id'] = 'Partes del transporte'
            reg['actualizacion'] = fields.date.today()
            reg['creacion'] = fields.datetime.now()
            self.env['actua.registro'].create(reg)

        if self.c_FiguraTransporte == True:
            
            data = {
                                    
                            "localizacion-mx":
                     { 
                     "Login":
                     { "rfc":rfc, "clave":clave
                     }, "Consulta":{ "Filtros":{ "fechadesde":"", "rangoinicial":"", "rangofinal":"", "paginar":"" } }} } 
                        
            headers =  {'content-type': 'application/json','timeout':'500000'}
            Respuesta =  requests.post(str(url) + "/c_FiguraTransporte", data=json.dumps(data), headers=headers)
            res =  json.loads(Respuesta.content.decode("utf-8"))                   
            _logger.error('Respuesta: %s', res)
            reg = dict()
            for c_FiguraTransporte in res:                 
                self.env['c_figuratransporte'].create(c_FiguraTransporte)
                _logger.info('\n******Fichero Cargado********\n')
            reg['modelo_id'] = 'Figura transporte'
            reg['actualizacion'] = fields.date.today()
            reg['creacion'] = fields.datetime.now()
            self.env['actua.registro'].create(reg)

        if self.c_ConfigAutoTransporte == True:
            
            data = {
                                    
                            "localizacion-mx":
                     { 
                     "Login":
                     { "rfc":rfc, "clave":clave
                     }, "Consulta":{ "Filtros":{ "fechadesde":"", "rangoinicial":"", "rangofinal":"", "paginar":"" } }} } 
                         
            headers =  {'content-type': 'application/json','timeout':'500000'}
            Respuesta =  requests.post(str(url) + "/c_ConfigAutoTransporte", data=json.dumps(data), headers=headers)
            res =  json.loads(Respuesta.content.decode("utf-8")) 
            _logger.error('res: %s', res)                 
            reg = dict()            
            for c_ConfigAutoTransporte in res:                             
                self.env['c_configautotransporte'].create(c_ConfigAutoTransporte)
                _logger.info('\n******Fichero Cargado********\n')
            reg['modelo_id'] = 'Configuración autotransporte'
            reg['actualizacion'] = fields.date.today()
            reg['creacion'] = fields.datetime.now()
            self.env['actua.registro'].create(reg)

        if self.c_SubTipoRem == True:
            
            data = {
                                    
                            "localizacion-mx":
                     { 
                     "Login":
                     { "rfc":rfc, "clave":clave
                     }, "Consulta":{ "Filtros":{ "fechadesde":"", "rangoinicial":"", "rangofinal":"", "paginar":"" } }} } 
                        
            headers =  {'content-type': 'application/json','timeout':'500000'}
            Respuesta =  requests.post(str(url) + "/c_SubTipoRem", data=json.dumps(data), headers=headers)
            res =  json.loads(Respuesta.content.decode("utf-8"))                   
            reg = dict()
            for c_SubTipoRem in res: 
                               
                self.env['c_subtiporem'].create(c_SubTipoRem)
                _logger.info('\n******Fichero Cargado********\n')
            reg['modelo_id'] = 'Tipo Remolque'
            reg['actualizacion'] = fields.date.today()
            reg['creacion'] = fields.datetime.now()
            self.env['actua.registro'].create(reg)
        
        if self.c_ContenedorMaritimo == True:
            
            data = {
                                    
                            "localizacion-mx":
                     { 
                     "Login":
                     { "rfc":rfc, "clave":clave
                     }, "Consulta":{ "Filtros":{ "fechadesde":"", "rangoinicial":"", "rangofinal":"", "paginar":"" } }} } 
                        
            headers =  {'content-type': 'application/json','timeout':'500000'}
            Respuesta =  requests.post(str(url) + "/c_ContenedorMaritimo", data=json.dumps(data), headers=headers)
            res =  json.loads(Respuesta.content.decode("utf-8"))                   
            reg = dict()
            _logger.error('res: %s', res)
            for c_ContenedorMaritimo in res:                           
                self.env['c_contenedormaritimo'].create(c_ContenedorMaritimo)
                _logger.info('\n******Fichero Cargado********\n')
            reg['modelo_id'] = 'Contenedor maritimo'
            reg['actualizacion'] = fields.date.today()
            reg['creacion'] = fields.datetime.now()
            self.env['actua.registro'].create(reg)

        if self.c_NumAutorizacionNaviero == True:
            
            data = {
                                    
                            "localizacion-mx":
                     { 
                     "Login":
                     { "rfc":rfc, "clave":clave
                     }, "Consulta":{ "Filtros":{ "fechadesde":"", "rangoinicial":"", "rangofinal":"", "paginar":"" } }} } 
                         
            headers =  {'content-type': 'application/json','timeout':'500000'}
            Respuesta =  requests.post(str(url) + "/c_NumAutorizacionNaviero", data=json.dumps(data), headers=headers)
            res =  json.loads(Respuesta.content.decode("utf-8"))                   
            reg = dict()
            for c_NumAutorizacionNaviero in res:                                 
                self.env['c_numautorizacionnaviero'].create(c_NumAutorizacionNaviero)
                _logger.info('\n******Fichero Cargado********\n')
            reg['modelo_id'] = 'Numero de autorización agente naviero'
            reg['actualizacion'] = fields.date.today()
            reg['creacion'] = fields.datetime.now()
            self.env['actua.registro'].create(reg)

        if self.c_CodigoTransporteAereo == True:
            
            data = {
                                    
                            "localizacion-mx":
                     { 
                     "Login":
                     { "rfc":rfc, "clave":clave
                     }, "Consulta":{ "Filtros":{ "fechadesde":"", "rangoinicial":"", "rangofinal":"", "paginar":"" } }} } 
                         
            headers =  {'content-type': 'application/json','timeout':'500000'}
            Respuesta =  requests.post(str(url) + "/c_CodigoTransporteAereo", data=json.dumps(data), headers=headers)
            res =  json.loads(Respuesta.content.decode("utf-8"))                   
            reg = dict()            
            for c_CodigoTransporteAereo in res:                                  
                self.env['c_codigotransporteaereo'].create(c_CodigoTransporteAereo)
                _logger.info('\n******Fichero Cargado********\n')
            reg['modelo_id'] = 'Código transporte aéreo'
            reg['actualizacion'] = fields.date.today()
            reg['creacion'] = fields.datetime.now()
            self.env['actua.registro'].create(reg)

        if self.c_TipoDeServicio == True:
            
            data = {
                                    
                            "localizacion-mx":
                     { 
                     "Login":
                     { "rfc":rfc, "clave":clave
                     }, "Consulta":{ "Filtros":{ "fechadesde":"", "rangoinicial":"", "rangofinal":"", "paginar":"" } }} } 
                         

            headers =  {'content-type': 'application/json','timeout':'500000'}
            Respuesta =  requests.post(str(url) + "/c_TipoDeServicio", data=json.dumps(data), headers=headers)
            res =  json.loads(Respuesta.content.decode("utf-8"))                  
            _logger.error('data: %s ', res)
            reg = dict()
            for c_TipoDeServicio in res: 
                                       
                self.env['c_tipodeservicio'].create(c_TipoDeServicio)
                _logger.info('\n******Fichero Cargado********\n')
            reg['modelo_id'] = 'Tipo De Servicio'
            reg['actualizacion'] = fields.date.today()
            reg['creacion'] = fields.datetime.now()
            self.env['actua.registro'].create(reg)

        if self.c_DerechosDePaso == True:
            
            data = {
                                    
                            "localizacion-mx":
                     { 
                     "Login":
                     { "rfc":rfc, "clave":clave
                     }, "Consulta":{ "Filtros":{ "fechadesde":"", "rangoinicial":"", "rangofinal":"", "paginar":"" } }} } 
                         
            headers =  {'content-type': 'application/json','timeout':'500000'}
            Respuesta =  requests.post(str(url) + "/c_DerechosDePaso", data=json.dumps(data), headers=headers)
            res =  json.loads(Respuesta.content.decode("utf-8")) 
            _logger.error('res: %s', res)                  
            reg = dict()
           
            for c_DerechosDePaso in res:                                              
                self.env['c_derechosdepaso'].create(c_DerechosDePaso)
                _logger.info('\n******Fichero Cargado********\n')
            reg['modelo_id'] = 'Derechos De Paso'
            reg['actualizacion'] = fields.date.today()
            reg['creacion'] = fields.datetime.now()
            self.env['actua.registro'].create(reg)
        
        if self.c_TipoCarro == True:
            
            data =  {
                                                       
                                     
                            "localizacion-mx":
                     { 
                     "Login":
                     { "rfc":rfc, "clave":clave
                     }, "Consulta":{ "Filtros":{ "fechadesde":"", "rangoinicial":"", "rangofinal":"", "paginar":"" } }} } 
                                   
            headers =  {'content-type': 'application/json','timeout':'500000'}
            Respuesta =  requests.post(str(url) + "/c_TipoCarro", data=json.dumps(data), headers=headers)
            res =  json.loads(Respuesta.content.decode("utf-8"))  
            _logger.error('res: %s', res)                 
            reg = dict()
            
            for c_TipoCarro in res:                                                
                self.env['c_tipocarro'].create(c_TipoCarro)
                _logger.info('\n******Fichero Cargado********\n')
            reg['modelo_id'] = 'Tipo Carro'
            reg['actualizacion'] = fields.date.today()
            reg['creacion'] = fields.datetime.now()
            self.env['actua.registro'].create(reg)

        if self.c_Contenedor == True:
            
            data =  {
                                                       
                                     
                            "localizacion-mx":
                     { 
                     "Login":
                     { "rfc":rfc, "clave":clave
                     }, "Consulta":{ "Filtros":{ "fechadesde":"", "rangoinicial":"", "rangofinal":"", "paginar":"" } }} } 
                                
            headers =  {'content-type': 'application/json','timeout':'500000'}
            Respuesta =  requests.post(str(url) + "/c_Contenedor", data=json.dumps(data), headers=headers)
            res =  json.loads(Respuesta.content.decode("utf-8"))                   
            reg = dict()
            
            _logger.error('res: %s', res)
            for c_Contenedor in res:                                          
                self.env['c_contenedor'].create(c_Contenedor)
                _logger.info('\n******Fichero Cargado********\n')
            reg['modelo_id'] = 'Contenedor'
            reg['actualizacion'] = fields.date.today()
            reg['creacion'] = fields.datetime.now()
            self.env['actua.registro'].create(reg)

        if self.c_TipoDeTrafico == True:
            
            data = {
                                    
                            "localizacion-mx":
                     { 
                     "Login":
                     { "rfc":rfc, "clave":clave
                     }, "Consulta":{ "Filtros":{ "fechadesde":"", "rangoinicial":"", "rangofinal":"", "paginar":"" } }} } 
                         
            headers =  {'content-type': 'application/json','timeout':'500000'}
            Respuesta =  requests.post(str(url) + "/c_TipoDeTrafico", data=json.dumps(data), headers=headers)
            res =  json.loads(Respuesta.content.decode("utf-8"))                   
            
            reg = dict()
            for c_TipoDeTrafico in res:  
                
                self.env['c_tipodetrafico'].create(c_TipoDeTrafico)
                _logger.info('\n******Fichero Cargado********\n')
            reg['modelo_id'] = 'Tipo De Trafico'
            reg['actualizacion'] = fields.date.today()
            reg['creacion'] = fields.datetime.now()
            self.env['actua.registro'].create(reg)

        
        _logger.info('\n******Fin de la carga de Datos********\n')   
        #return self._reopen_wizard()
        return res
    
    def actualiza_catalogos(self):
        res = super(overall_config_wizard_sat_models_cfdi, self).actualiza_catalogos()
        webservice_url = self.env['ir.config_parameter'].sudo().get_param('webservice.url')      
        rfc = self.env['ir.config_parameter'].sudo().get_param('webservice.rfc_web')
        clave = self.env['ir.config_parameter'].sudo().get_param('webservice.password')
        if webservice_url == 'test':
            url = self.env['ir.config_parameter'].sudo().get_param('webservice.url_name_prue')
        if webservice_url == 'product':
            url = self.env['ir.config_parameter'].sudo().get_param('webservice.url_name_produc')
        if not rfc or not clave or not url: 
            raise UserError(_("Error!\nlos Datos de conexión al webservice son incorrectos o estan vacios .\n\n" 'RFC: %s\n' 'Clave: %s\n' 'URL: %s\n') % (rfc, clave, url))
              
        if self.c_ClaveTipoCarga == True:
            registro = self.env['actua.registro'].search([('modelo_id', '=', 'Clave tipo carga')])
            fecha_actu = datetime.datetime.strptime(str(registro.actualizacion), '%Y-%m-%d')
            fecha_actua = fecha_actu.strftime('%d-%m-%Y')
            data = {
                                    
                            "localizacion-mx":
                     { 
                     "Login":
                     { "rfc":rfc, "clave":clave
                     }, "Consulta":{ "Filtros":{ "fechadesde": fecha_actua, "rangoinicial":"", "rangofinal":"", "paginar":"" }  } } } 
                         
            _logger.error('data: %s ', data)
            headers =  {'content-type': 'application/json','timeout':'500000'}
            Respuesta =  requests.post(str(url) + "/c_Aduana", data=json.dumps(data), headers=headers)                
            res =  json.loads(Respuesta.content.decode("utf-8"))
            _logger.error('Respuestas: %s', aduanas)
            for c_ClaveTipoCarga in res: 
                
                tipocarga = self.env['c_clavetipocarga'].search([('Clave', '=', c_ClaveTipoCarga['Clave'])])

                if tipocarga:
                    tipocarga.write(c_ClaveTipoCarga)  

                else:
                    tipocarga.create(aduana)                           
                
                _logger.info('\n******Fichero Actualizado********\n')
            registro.actualizacion = fields.date.today()
            return res


       

    @api.onchange('sat_cp')
    def select_catalogos(self):
        if self.sat_cp == True:
            self.c_ClaveTipoCarga = True                        
            self.c_ConfigMaritima = True            
            self.c_CveTransporte = True
            self.c_TipoEstacion = True
            self.c_Estaciones = True
            self.c_ClaveUnidadPeso = True
            self.c_MaterialPeligroso = True
            self.c_TipoEmbalaje = True            
            self.c_TipoPermiso = True
            self.c_ParteTransporte = True
            self.c_FiguraTransporte = True
            self.c_ConfigAutoTransporte = True            
            self.c_SubTipoRem = True
            self.c_ContenedorMaritimo = True
            self.c_NumAutorizacionNaviero = True
            self.c_CodigoTransporteAereo = True
            self.c_TipoDeServicio = True
            self.c_DerechosDePaso = True
            self.c_TipoCarro = True
            self.c_Contenedor = True
            self.c_TipoDeTrafico = True            

        else:
            self.c_ClaveTipoCarga = False                        
            self.c_ConfigMaritima = False            
            self.c_CveTransporte = False
            self.c_TipoEstacion = False
            self.c_Estaciones = False
            self.c_ClaveUnidadPeso = False
            self.c_MaterialPeligroso = False
            self.c_TipoEmbalaje = False            
            self.c_TipoPermiso = False
            self.c_ParteTransporte = False
            self.c_FiguraTransporte = False
            self.c_ConfigAutoTransporte = False            
            self.c_SubTipoRem = False
            self.c_ContenedorMaritimo = False
            self.c_NumAutorizacionNaviero = False
            self.c_CodigoTransporteAereo = False
            self.c_TipoDeServicio = False
            self.c_DerechosDePaso = False
            self.c_TipoCarro = False
            self.c_Contenedor = False
            self.c_TipoDeTrafico = False

        
   
    
    
    
        


   
