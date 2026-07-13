# -*- encoding: utf-8 -*-

from odoo import api, fields, models, _
import requests
import json
import urllib
import logging
_logger = logging.getLogger(__name__)
from odoo.exceptions import UserError, RedirectWarning, ValidationError
from . import update_mx_data
from odoo.tools import DEFAULT_SERVER_DATETIME_FORMAT, DEFAULT_SERVER_DATE_FORMAT
from odoo.tools.misc import DEFAULT_SERVER_DATE_FORMAT, format_date
import datetime
from datetime import timedelta, datetime
import math
import time
import datetime
#import date





class overall_config_wizard_sat_models_cfdi(models.TransientModel):
    _name = 'overall.config.wizard.sat.models.cfdi'
    
    
    sat_cfdi = fields.Boolean('Todos')
    sat_ce = fields.Boolean('Todos')
    sat_colonia = fields.Boolean('Colonias')        
    sat_codigo_postal = fields.Boolean('Códigos Postales')    
    sat_localidad = fields.Boolean('Localidades')
    sat_estados = fields.Boolean('Estados')
    sat_aduana = fields.Boolean('Aduanas')
    sat_paises = fields.Boolean('Paises')
    sat_municipio = fields.Boolean('Municipios')
    sat_producto = fields.Boolean('Productos/Servicios')    
    sat_udm = fields.Boolean('Unidades de Medida')
    sat_uso_cfdi = fields.Boolean('Uso de CFDI')
    sat_pedimento = fields.Boolean('Pedimentos Aduanales')
    sat_arancel = fields.Boolean('Fracciones Arancelarias (Comercio Exterior)')
    sat_bancos = fields.Boolean('Bancos')
    sat_regimen_fiscal = fields.Boolean('Regimen Fiscal')
    sat_impuestos = fields.Boolean('Impuestos')
    sat_formas_pago = fields.Boolean('Formas de Pago')
    sat_metodo_pago = fields.Boolean('Metodos de Pago')
    sat_tipos_relacion = fields.Boolean('Tipos Relación CFDI')
    sat_patentes_aduanales = fields.Boolean('Patentes Aduanales')
    sat_moneda = fields.Boolean('Monedas')
    sat_tipo_comprobante = fields.Boolean('Tipo de Comprobante')
    tipo_poliza = fields.Boolean('Tipo de Pólizas')
    sat_codigo_agrupador = fields.Boolean('Códigos Agrupadores')
    load_data = fields.Boolean('Informacion Cargada')
    action_status = fields.Text('Notas de Carga de Datos')
    sat_tasaocuota = fields.Boolean('Tasa o Cuota')
    sat_tipofactor = fields.Boolean('Tipo Factor')
    sat_clavepedemiento = fields.Boolean ('Claves de Pedimento')
    sat_tipooperacion = fields.Boolean('Tipos de Operación')
    sat_traslado = fields.Boolean('Motivo Traslado')
    sat_metodopago = fields.Boolean('Métodos de Pago SAT')
    pacs = fields.Boolean('Pacs')
    sat_meses = fields.Boolean('Meses')
    sat_periodicidad = fields.Boolean('Periodicidad')
    sat_objetoimp = fields.Boolean('ObjetoImp')        
    sat_exportacion = fields.Boolean('Exportación') 

    @api.model
    def _reopen_wizard(self):
        return { 'type'     : 'ir.actions.act_window',
                 'res_id'   : self.id,
                 'view_mode': 'form',
                 'view_type': 'form',
                 'res_model': 'overall.config.wizard.sat.models.cfdi',
                 'target'   : 'new',
                 'name'     : 'Carga de Catalogos para la Facturacion CFDI 3.3'}

    
    Paginas = 0
    RegPorPagina = 40000
    RegInicial = 0
    CuantosRegistros = 0
    RegistrosPendientes =0
    Pagina = 1
    Archivo_registros = 0

    #@api.model    
    def carga_catalogos(self, Desde=0, Cuantos=0):
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
        
            
        Respuesta = requests.get(str(url) + "/version")
        datos =  json.loads(Respuesta.content.decode("utf-8"))
        ad = dict()
        version_ws = datos["Version_ws"]
        ad["Version_ws"] = version_ws
        ad["Version_sat"] = datos["Version_sat"]
        ad["Version_sat"] = datos["Version_sat"]
        #ad["Actualizacion"] = datos["Actualizacion"]
        #ad["Creacion"] = datos["Creacion"]
        ad["Notas"] = datos["Notas"]   
        #ad["FechaLiberacion"] = ""#datos["FechaLiberacion"]     
        self.env['actua.historial'].create(ad)
        
        if self.sat_aduana == True:            
            data = {
                                    
                            "localizacion-mx":
                     { 
                     "Login":
                     { "rfc":rfc, "clave":clave
                     }, "Consulta":{ "Filtros":{ "fechadesde":"", "rangoinicial":"", "rangofinal":"", "paginar":"" }  } } } 
                         
            _logger.error('data: %s ', data)
            headers =  {'content-type': 'application/json','timeout':'500000'}
            Respuesta =  requests.post(str(url) + "/c_Aduana", data=json.dumps(data), headers=headers)                
            aduanas =  json.loads(Respuesta.content.decode("utf-8"))
            reg = dict()
            ad = dict()
            for aduana in aduanas: 
                ad['code'] = aduana['code']
                ad['name'] = aduana['name']
                _logger.info('\n******Cargando Fichero Aduanas********\n')
                                            
                self.env['sat.aduana'].create(ad)

                _logger.info('\n******Fichero Cargado********\n')
            reg['modelo_id'] = 'Aduanas'
            reg['actualizacion'] = fields.date.today()
            reg['creacion'] = fields.datetime.now()
            self.env['actua.registro'].create(reg)

        if self.sat_producto == True:
            Paginas = 0
            RegPorPagina = 30000
            RegInicial = 0
            CuantosRegistros = 0
            RegistrosPendientes =0
            Pagina = 1
            Archivo_registros = 0
            req = requests.get(str(url) + "/registros/c_ClaveProdServ")
            respuesta = json.loads(req.text)
            _logger.error("Numero de registros: %s", respuesta)
            
            Archivo_registros = respuesta['registros']
            RegistrosPendientes = Archivo_registros
            Paginas = Archivo_registros / RegPorPagina
            pag = math.ceil(Paginas)
            _logger.error("Numero de paginas: %s", pag)
            
            def descarga(Desde, Cuantos):
                data = {

                                "localizacion-mx":
                         {
                         "Login":
                         { "rfc":rfc, "clave":clave
                         }, "Consulta":{ "Filtros":{ "fechadesde":"2019-01-01", "rangoinicial":str(Desde), "rangofinal":str(Cuantos), "paginar":1 } }}}
                _logger.error("Datos: %s", data)
                headers =  {'content-type': 'application/json','timeout':'500000'}
                Respuesta =  requests.post(str(url) + "/c_ClaveProdServ", data=json.dumps(data), headers=headers)
                res =  json.loads(Respuesta.content.decode("utf-8"))
                _logger.error('PRoductos: %s', res)
                reg = dict()
                ad = dict()
                for product in res:                  
                    ad['code'] = product['code']
                    ad['franja_fronteriza'] = product['franja_fronteriza']
                    ad['name'] = product['name']
                    ad['incluir_iva_trasladado'] = product['incluir_iva_trasladado']
                    ad['incluir_ieps_trasladado'] = product['incluir_ieps_trasladado']
                    ad['MaterialPeligroso'] = product['MaterialPeligroso']
                    self.env['sat.producto'].create(ad)
                    _logger.info('\n******Fichero Cargado********\n')
                reg['modelo_id'] = 'Productos'
                reg['actualizacion'] = fields.date.today()
                reg['creacion'] = fields.datetime.now()
                self.env['actua.registro'].create(reg)
            while RegistrosPendientes > 0:
                if RegistrosPendientes > RegPorPagina:
                    cuantos = CuantosRegistros + RegPorPagina
                    CuantosRegistros = RegPorPagina

                    _logger.error('Pagina1: %s', str(Pagina) + ' ' + str(RegPorPagina))
                    RegistrosPendientes -= RegPorPagina
                else:
                    cuantos = CuantosRegistros + RegistrosPendientes
                    CuantosRegistros = RegistrosPendientes
                    _logger.error('Pagina2: %s', str(Pagina) + ' ' + str(RegistrosPendientes))
                    RegistrosPendientes -= RegistrosPendientes

                descarga(RegInicial, CuantosRegistros)
                Pagina+=1
                RegInicial = cuantos
            
            

        if self.sat_paises == True:
            
            data = {
                                    
                            "localizacion-mx":
                     { 
                     "Login":
                     { "rfc":rfc, "clave":clave
                     }, "Consulta":{ "Filtros":{ "fechadesde":"", "rangoinicial":"", "rangofinal":"", "paginar":"" } }} }
                       
            _logger.error('data: %s ', data)
            headers =  {'content-type': 'application/json','timeout':'500000'}
            Respuesta =  requests.post(str(url) + "/c_Pais", data=json.dumps(data), headers=headers)
            res =  json.loads(Respuesta.content.decode("utf-8"))                  
            _logger.error('data: %s ', res)
            reg = dict()
            ad = dict()
            for pais in res: 
                ad['code'] = pais['code']
                ad['name'] = pais['name']
                
                _logger.info('\n******Cargando Fichero Paises********\n')                                            
                self.env['res.country.sat.code'].create(pais)
                _logger.info('\n******Fichero Cargado********\n')
            reg['modelo_id'] = 'Paises'
            reg['actualizacion'] = fields.date.today()
            reg['creacion'] = fields.datetime.now()
            self.env['actua.registro'].create(reg)

        if self.sat_paises == True:
            self.update_countrys_sat()
            
        if self.sat_colonia == True:
            Paginas = 0
            RegPorPagina = 40000
            RegInicial = 0
            CuantosRegistros = 0
            RegistrosPendientes =0
            Pagina = 1
            Archivo_registros = 0
            req = requests.get(str(url) + "/registros/c_Colonia")        
            respuesta = json.loads(req.text)
            _logger.error("Numero de registros: %s", respuesta)
            
            Archivo_registros = respuesta['registros']
            RegistrosPendientes = Archivo_registros
            Paginas = Archivo_registros / RegPorPagina
            pag = math.ceil(Paginas)
            _logger.error("Numero de paginas: %s", pag)
            def descarga(Desde, Cuantos):
                data = {"localizacion-mx":{"login":{"rfc":rfc,"clave":clave},
                "Consulta":{"Filtros":{"fechadesde":"2019-01-01","rangoinicial":str(Desde),"rangofinal":str(Cuantos),"paginar":1}}}}
                _logger.error('Colonias: %s', data)
                headers =  {'content-type': 'application/json','timeout':'500000'}
                Respuesta =  requests.post(str(url) + "/c_Colonia", data=json.dumps(data), headers=headers)
                res =  json.loads(Respuesta.content.decode("utf-8"))                 
                _logger.error('Colonias: %s', res)
                reg = dict()
                for col in res:
                                                
                    self.env['res.colonia.zip.sat.code'].create(col)
                    _logger.info('\n******Fichero Cargado********\n')

                reg['modelo_id'] = 'Colonias'
                reg['actualizacion'] = fields.Date.today()
                reg['creacion'] = fields.datetime.now()
                self.env['actua.registro'].create(reg)
            while RegistrosPendientes > 0:
                if RegistrosPendientes > RegPorPagina:
                    cuantos = CuantosRegistros + RegPorPagina
                    CuantosRegistros = RegPorPagina
                    
                    _logger.error('Pagina1: %s', str(Pagina) + ' ' + str(RegPorPagina))
                    RegistrosPendientes -= RegPorPagina
                else:
                    cuantos = CuantosRegistros + RegistrosPendientes
                    CuantosRegistros = RegistrosPendientes                    
                    _logger.error('Pagina2: %s', str(Pagina) + ' ' + str(RegistrosPendientes))
                    RegistrosPendientes -= RegistrosPendientes

                descarga(RegInicial, CuantosRegistros)
                Pagina+=1
                RegInicial = cuantos
        if self.sat_codigo_postal == True:
            Paginas = 0
            RegPorPagina = 40000
            RegInicial = 0
            CuantosRegistros = 0
            RegistrosPendientes =0
            Pagina = 1
            Archivo_registros = 0
            req = requests.get(str(url) + "/registros/c_CodigoPostal")        
            respuesta = json.loads(req.text)
            _logger.error("Numero de registros: %s", respuesta)
            #self.RegPorPagina = 40000
            Archivo_registros = respuesta['registros']
            RegistrosPendientes = Archivo_registros
            Paginas = Archivo_registros / RegPorPagina
            pag = math.ceil(Paginas)
            _logger.error("Numero de paginas: %s", pag)

            def descarga(Desde, Cuantos):
                data = {
                                        
                                "localizacion-mx":
                         { 
                         "Login":
                         { "rfc":rfc, "clave":clave
                         }, "Consulta":{ "Filtros":{ "fechadesde":"2019-01-01", "rangoinicial":str(Desde), "rangofinal":str(Cuantos), "paginar":1 }}}} 
                _logger.error("Datos: %s", data)         
                headers =  {'content-type': 'application/json','timeout':'500000'}
                Respuesta =  requests.post(str(url) + "/c_CodigoPostal", data=json.dumps(data), headers=headers)
                res =  json.loads(Respuesta.content.decode("utf-8"))
                _logger.error('Codigo postal: %s', res) 
                reg = dict()
                ad = dict()
                for cp in res: 
                    ad['code'] = cp['code'] 
                    ad['state_sat_code'] = cp['state_sat_code']
                    ad['township_sat_code'] = cp['township_sat_code']
                    ad['locality_sat_code'] = cp['locality_sat_code']
                    ad['franja_fronteriza'] = cp['franja_fronteriza']

                    self.env['res.country.zip.sat.code'].create(ad)
                    _logger.info('\n******Fichero Cargado********\n')

                reg['modelo_id'] = 'Códigos Postales'
                reg['actualizacion'] = fields.date.today()
                reg['creacion'] = fields.datetime.now()
                self.env['actua.registro'].create(reg)

            while RegistrosPendientes > 0:
                if RegistrosPendientes > RegPorPagina:
                    cuantos = CuantosRegistros + RegPorPagina
                    CuantosRegistros = RegPorPagina                    
                    _logger.error('Pagina1: %s', str(Pagina) + ' ' + str(RegPorPagina))
                    RegistrosPendientes -= RegPorPagina
                else:
                    cuantos = CuantosRegistros + RegistrosPendientes
                    CuantosRegistros = RegistrosPendientes                    
                    _logger.error('Pagina2: %s', str(Pagina) + ' ' + str(RegistrosPendientes))
                    RegistrosPendientes -= RegistrosPendientes
                descarga(RegInicial, CuantosRegistros)
                Pagina+=1
                RegInicial = cuantos        
        
        if self.sat_localidad == True:
            
            data = {
                                    
                            "localizacion-mx":
                     { 
                     "Login":
                     { "rfc":rfc, "clave":clave
                     }, "Consulta":{ "Filtros":{ "fechadesde":"", "rangoinicial":"", "rangofinal":"", "paginar":"" } }} }
                       
            headers =  {'content-type': 'application/json','timeout':'500000'}
            Respuesta =  requests.post(str(url) + "/c_Localidad", data=json.dumps(data), headers=headers)
            res =  json.loads(Respuesta.content.decode("utf-8"))                 
            reg = dict()
            for localidad in res: 
                _logger.info('\n******Cargando Fichero Localidades********\n')                                            
                self.env['res.country.locality.sat.code'].create(localidad)
                _logger.info('\n******Fichero Cargado********\n')
            reg['modelo_id'] = 'Localidades'
            reg['actualizacion'] = fields.date.today()
            reg['creacion'] = fields.datetime.now()
            self.env['actua.registro'].create(reg)
        
        if self.sat_estados == True:
            
            data = {
                                    
                            "localizacion-mx":
                     { 
                     "Login":
                     { "rfc":rfc, "clave":clave
                     }, "Consulta":{ "Filtros":{ "fechadesde":"", "rangoinicial":"", "rangofinal":"", "paginar":"" } }} } 
                         
            headers =  {'content-type': 'application/json','timeout':'500000'}
            Respuesta =  requests.post(str(url) + "/c_Estado", data=json.dumps(data), headers=headers)
            res =  json.loads(Respuesta.content.decode("utf-8"))                 
            reg = dict()
            for estados in res: 
                _logger.info('\n******Cargando Fichero Estados********\n')                                          
                self.env['res.country.state.sat.code'].create(estados)
                _logger.info('\n******Fichero Cargado********\n')
            reg['modelo_id'] = 'Estados'
            reg['actualizacion'] = fields.date.today()
            reg['creacion'] = fields.datetime.now()
            self.env['actua.registro'].create(reg)
        if self.sat_estados == True:
            self.update_countrys_states_sat()
            _logger.error('Actualizacion: %s', self.update_countrys_states_sat)

        if self.sat_municipio == True:
            
            data = {
                                    
                            "localizacion-mx":
                     { 
                     "Login":
                     { "rfc":rfc, "clave":clave
                     }, "Consulta":{ "Filtros":{ "fechadesde":"", "rangoinicial":"", "rangofinal":"", "paginar":"" } }} }
                         
            headers =  {'content-type': 'application/json','timeout':'500000'}
            Respuesta =  requests.post(str(url) + "/c_Municipio", data=json.dumps(data), headers=headers)
            res =  json.loads(Respuesta.content.decode("utf-8"))                  
            reg = dict()
            for munip in res: 
                _logger.info('\n******Cargando Fichero Municipios********\n')                                          
                self.env['res.country.township.sat.code'].create(munip)
                _logger.info('\n******Fichero Cargado********\n')
            reg['modelo_id'] = 'Municipios'
            reg['actualizacion'] = fields.date.today()
            reg['creacion'] = fields.datetime.now()
            self.env['actua.registro'].create(reg)

        if self.sat_udm == True:
            
            data = {
                                    
                            "localizacion-mx":
                     { 
                     "Login":
                     { "rfc":rfc, "clave":clave
                     }, "Consulta":{ "Filtros":{ "fechadesde":"", "rangoinicial":"", "rangofinal":"", "paginar":"" } } } } 
                         
            headers = {'content-type': 'application/json','timeout':'500000'}
            Respuesta =  requests.post(str(url) + "/c_ClaveUnidad", data=json.dumps(data), headers=headers)
            res =  json.loads(Respuesta.content.decode("utf-8"))                   
            reg = dict()
            for um in res: 
                _logger.info('\n******Cargando Fichero Unidades de Medida********\n')                          
                self.env['sat.udm'].create(um)
                _logger.info('\n******Fichero Cargado********\n')
            reg['modelo_id'] = 'Unidades de Medida'
            reg['actualizacion'] = fields.date.today()
            reg['creacion'] = fields.datetime.now()
            self.env['actua.registro'].create(reg)

        if self.sat_uso_cfdi == True:
            
            data = {
                                    
                            "localizacion-mx":
                     { 
                     "Login":
                     { "rfc":rfc, "clave":clave
                     }, "Consulta":{ "Filtros":{ "fechadesde":"", "rangoinicial":"", "rangofinal":"", "paginar":"" } }} } 
                                          
                   
            headers =  {'content-type': 'application/json','timeout':'500000'}
            Respuesta =  requests.post(str(url) + "/c_UsoCFDI", data=json.dumps(data), headers=headers)
            res =  json.loads(Respuesta.content.decode("utf-8")) 
            _logger.error('res: %s', res)                 
            reg = dict()
            for cfdi in res: 
                _logger.info('\n******Cargando Fichero Uso Cfdi********\n')                                             
                self.env['sat.uso.cfdi'].create(cfdi)
                _logger.info('\n******Fichero Cargado********\n')
            reg['modelo_id'] = 'Uso de CFDI'
            reg['actualizacion'] = fields.date.today()
            reg['creacion'] = fields.datetime.now()
            self.env['actua.registro'].create(reg)

        if self.sat_pedimento == True:            

            data = {
                                    
                            "localizacion-mx":
                     { 
                     "Login":
                     { "rfc":rfc, "clave":clave
                     }, "Consulta":{ "Filtros":{ "fechadesde":"", "rangoinicial":"", "rangofinal":"", "paginar":"" } } } } 
                        
            headers =  {'content-type': 'application/json','timeout':'500000'}
            Respuesta =  requests.post(str(url) + "/c_pedimentoaduanal", data=json.dumps(data), headers=headers)
            res =  json.loads(Respuesta.content.decode("utf-8"))                   
            _logger.error('Respuesta: %s', res)
            ad = dict()  
            reg = dict()  
            for patente in res: 
                ad['name_1'] = patente['name']
                ad['cantidad'] = patente['Cantidad']
                ad['ejercicio'] = patente['ejercicio']
                ad['start_date'] = patente['start_date']          
                #ad['aduana_code'] = patente['c_PedimentoAduanalID']                    
                self.env['sat.patente'].create(ad)
                _logger.info('\n******Fichero Cargado********\n')
            reg['modelo_id'] = 'Pedimentos'
            reg['actualizacion'] = fields.date.today()
            reg['creacion'] = fields.datetime.now()
            self.env['actua.registro'].create(reg)

        if self.sat_arancel == True:
            
            data = {
                                    
                            "localizacion-mx":
                     { 
                     "Login":
                     { "rfc":rfc, "clave":clave
                     }, "Consulta":{ "Filtros":{ "fechadesde":"", "rangoinicial":"", "rangofinal":"", "paginar":"" } } } } 
                         
            headers =  {'content-type': 'application/json','timeout':'500000'}
            Respuesta =  requests.post(str(url) + "/c_FraccionArancelaria", data=json.dumps(data), headers=headers)
            res =  json.loads(Respuesta.content.decode("utf-8"))
            _logger.error('res: %s', res)   
            ad = dict()               
            reg = dict()
            for arancel in res: 
                ad['code'] = arancel['code']
                ad['name'] = arancel['name']
                ad['criterio'] = arancel['criterio']
                ad['unidad_de_medida'] = arancel['UnidadDeMedida']
                ad['impuesto_exportacion'] = arancel['IMP']

                _logger.info('\n******Cargando Fichero Aranceles********\n')                                                       
                self.env['sat.arancel'].create(ad)
                _logger.info('\n******Fichero Cargado********\n')

            reg['modelo_id'] = 'Aranceles'
            reg['actualizacion'] = fields.date.today()
            reg['creacion'] = fields.datetime.now()
            self.env['actua.registro'].create(reg)

        if self.sat_bancos == True:
            
            data = {
                                    
                            "localizacion-mx":
                     { 
                     "Login":
                     { "rfc":rfc, "clave":clave
                     }, "Consulta":{ "Filtros":{ "fechadesde":"", "rangoinicial":"", "rangofinal":"", "paginar":"" } } } } 
                        
            headers =  {'content-type': 'application/json','timeout':'500000'}
            Respuesta =  requests.post(str(url) + "/c_Banco", data=json.dumps(data), headers=headers)
            res =  json.loads(Respuesta.content.decode("utf-8"))   
            _logger.error('res: %s', res)            
            reg = dict()
            ad = dict()
            for banco in res: 
                ad['bic'] = banco['bic']
                ad['code'] = banco['code']
                ad['name'] = banco['name']
                _logger.info('\n******Cargando Fichero Bancos********\n')                                                                       
                self.env['eaccount.bank'].create(ad)
                _logger.info('\n******Fichero Cargado********\n')
            reg['modelo_id'] = 'Bancos'
            reg['actualizacion'] = fields.date.today()
            reg['creacion'] = fields.datetime.now()
            self.env['actua.registro'].create(reg)

        if self.sat_regimen_fiscal == True:
            
            data = {
                                    
                            "localizacion-mx":
                     { 
                     "Login":
                     { "rfc":rfc, "clave":clave
                     }, "Consulta":{ "Filtros":{ "fechadesde":"", "rangoinicial":"", "rangofinal":"", "paginar":"" } }} } 
                        
            headers =  {'content-type': 'application/json','timeout':'500000'}
            Respuesta =  requests.post(str(url) + "/c_RegimenFiscal", data=json.dumps(data), headers=headers)
            res =  json.loads(Respuesta.content.decode("utf-8"))                   
            _logger.error('Respuesta: %s', res)
            reg = dict()
            for rg in res: 
                _logger.info('\n******Cargando Fichero Regimen Fiscal********\n')                                                                                            
                self.env['sat.regimen.fiscal'].create(rg)
                _logger.info('\n******Fichero Cargado********\n')
            reg['modelo_id'] = 'Regimen Fiscal'
            reg['actualizacion'] = fields.date.today()
            reg['creacion'] = fields.datetime.now()
            self.env['actua.registro'].create(reg)

        if self.sat_impuestos == True:
            
            data = {
                                    
                            "localizacion-mx":
                     { 
                     "Login":
                     { "rfc":rfc, "clave":clave
                     }, "Consulta":{ "Filtros":{ "fechadesde":"", "rangoinicial":"", "rangofinal":"", "paginar":"" } }} } 
                         
            headers =  {'content-type': 'application/json','timeout':'500000'}
            Respuesta =  requests.post(str(url) + "/c_Impuesto", data=json.dumps(data), headers=headers)
            res =  json.loads(Respuesta.content.decode("utf-8")) 
            _logger.error('res: %s', res)                 
            reg = dict()    
            ad = dict()
            for impu in res: 
                ad['code'] = impu['code']
                ad['name'] = impu['name']
                ad['retencion'] = impu['Retencion']
                ad['traslado'] = impu['Traslado']
                ad['tipo'] = 'federal'
                _logger.info('\n******Cargando Fichero Impuestos********\n')                
                self.env['sat.impuesto'].create(ad)
                _logger.info('\n******Fichero Cargado********\n')
            reg['modelo_id'] = 'Impuestos'
            reg['actualizacion'] = fields.date.today()
            reg['creacion'] = fields.datetime.now()
            self.env['actua.registro'].create(reg)

        if self.sat_formas_pago == True:
            
            data = {
                                    
                            "localizacion-mx":
                     { 
                     "Login":
                     { "rfc":rfc, "clave":clave
                     }, "Consulta":{ "Filtros":{ "fechadesde":"", "rangoinicial":"", "rangofinal":"", "paginar":"" } }} } 
                        
            headers =  {'content-type': 'application/json','timeout':'500000'}
            Respuesta =  requests.post(str(url) + "/c_FormaPago", data=json.dumps(data), headers=headers)
            res =  json.loads(Respuesta.content.decode("utf-8"))                   
            reg = dict()
            for formas in res: 
                _logger.info('\n******Cargando Fichero Formas de Pago********\n')                
                self.env['pay.method'].create(formas)
                _logger.info('\n******Fichero Cargado********\n')
            reg['modelo_id'] = 'Formas de Pago'
            reg['actualizacion'] = fields.date.today()
            reg['creacion'] = fields.datetime.now()
            self.env['actua.registro'].create(reg)
        
        if self.sat_metodo_pago == True:
            
            data = {
                                    
                            "localizacion-mx":
                     { 
                     "Login":
                     { "rfc":rfc, "clave":clave
                     }, "Consulta":{ "Filtros":{ "fechadesde":"", "rangoinicial":"", "rangofinal":"", "paginar":"" } }} } 
                        
            headers =  {'content-type': 'application/json','timeout':'500000'}
            Respuesta =  requests.post(str(url) + "/c_MetodoPago", data=json.dumps(data), headers=headers)
            res =  json.loads(Respuesta.content.decode("utf-8"))                   
            reg = dict()
            _logger.error('res: %s', res)
            for mp in res: 
                _logger.info('\n******Cargando Fichero Método de Pago********\n')                
                self.env['sat.metodo.pago'].create(mp)
                _logger.info('\n******Fichero Cargado********\n')
            reg['modelo_id'] = 'Metodos de Pagos'
            reg['actualizacion'] = fields.date.today()
            reg['creacion'] = fields.datetime.now()
            self.env['actua.registro'].create(reg)

        if self.sat_tipos_relacion == True:
            
            data = {
                                    
                            "localizacion-mx":
                     { 
                     "Login":
                     { "rfc":rfc, "clave":clave
                     }, "Consulta":{ "Filtros":{ "fechadesde":"", "rangoinicial":"", "rangofinal":"", "paginar":"" } }} } 
                         
            headers =  {'content-type': 'application/json','timeout':'500000'}
            Respuesta =  requests.post(str(url) + "/c_TipoRelacion", data=json.dumps(data), headers=headers)
            res =  json.loads(Respuesta.content.decode("utf-8"))                   
            reg = dict()
            for tipos in res: 
                _logger.info('\n******Cargando Fichero Tipos de Relacion********\n')                
                self.env['sat.tipo.relacion.cfdi'].create(tipos)
                _logger.info('\n******Fichero Cargado********\n')
            reg['modelo_id'] = 'Tipos Relacion CFDI'
            reg['actualizacion'] = fields.date.today()
            reg['creacion'] = fields.datetime.now()
            self.env['actua.registro'].create(reg)

        if self.sat_patentes_aduanales == True:
            
            data = {
                                    
                            "localizacion-mx":
                     { 
                     "Login":
                     { "rfc":rfc, "clave":clave
                     }, "Consulta":{ "Filtros":{ "fechadesde":"", "rangoinicial":"", "rangofinal":"", "paginar":"" } }} } 
                         
            headers =  {'content-type': 'application/json','timeout':'500000'}
            Respuesta =  requests.post(str(url) + "/c_PatenteAduanal", data=json.dumps(data), headers=headers)
            res =  json.loads(Respuesta.content.decode("utf-8"))                   
            reg = dict()
            ad = dict()
            for tipos in res: 
                _logger.info('\n******Cargando Fichero Patentes Aduanales********\n')                
                ad["code"] = tipos["code"]                       
                self.env['sat.patente.aduanal'].create(ad)
                _logger.info('\n******Fichero Cargado********\n')
            reg['modelo_id'] = 'Patentes Aduanales'
            reg['actualizacion'] = fields.date.today()
            reg['creacion'] = fields.datetime.now()
            self.env['actua.registro'].create(reg)

        if self.sat_moneda == True:
            
            data = {
                                    
                            "localizacion-mx":
                     { 
                     "Login":
                     { "rfc":rfc, "clave":clave
                     }, "Consulta":{ "Filtros":{ "fechadesde":"", "rangoinicial":"", "rangofinal":"", "paginar":"" } }} } 
                         

            headers =  {'content-type': 'application/json','timeout':'500000'}
            Respuesta =  requests.post(str(url) + "/c_Moneda", data=json.dumps(data), headers=headers)
            res =  json.loads(Respuesta.content.decode("utf-8"))                  
            _logger.error('data: %s ', res)
            reg = dict()
            for tipos in res: 
                _logger.info('\n******Cargando Fichero Monedas********\n')                          
                self.env['eaccount.currency'].create(tipos)
                _logger.info('\n******Fichero Cargado********\n')
            reg['modelo_id'] = 'Monedas'
            reg['actualizacion'] = fields.date.today()
            reg['creacion'] = fields.datetime.now()
            self.env['actua.registro'].create(reg)

        if self.sat_tipo_comprobante == True:
            
            data = {
                                    
                            "localizacion-mx":
                     { 
                     "Login":
                     { "rfc":rfc, "clave":clave
                     }, "Consulta":{ "Filtros":{ "fechadesde":"", "rangoinicial":"", "rangofinal":"", "paginar":"" } }} } 
                         
            headers =  {'content-type': 'application/json','timeout':'500000'}
            Respuesta =  requests.post(str(url) + "/c_TipoComprobante", data=json.dumps(data), headers=headers)
            res =  json.loads(Respuesta.content.decode("utf-8")) 
            _logger.error('res: %s', res)                  
            reg = dict()
            ad = dict()
            for compro in res: 
                ad['code'] = compro['code']
                ad['name'] = compro['name']
                _logger.info('\n******Cargando Fichero Tipos de Comprobante********\n')                                
                self.env['sat.tipo.comprobante'].create(ad)
                _logger.info('\n******Fichero Cargado********\n')
            reg['modelo_id'] = 'Tipo de Comprobante'
            reg['actualizacion'] = fields.date.today()
            reg['creacion'] = fields.datetime.now()
            self.env['actua.registro'].create(reg)
        
        if self.tipo_poliza == True:
            
            data =  {
                                                       
                                     
                            "localizacion-mx":
                     { 
                     "Login":
                     { "rfc":rfc, "clave":clave
                     }, "Consulta":{ "Filtros":{ "fechadesde":"", "rangoinicial":"", "rangofinal":"", "paginar":"" } }} } 
                                   
            headers =  {'content-type': 'application/json','timeout':'500000'}
            Respuesta =  requests.post(str(url) + "/c_tiposdepolizas", data=json.dumps(data), headers=headers)
            res =  json.loads(Respuesta.content.decode("utf-8"))  
            _logger.error('res: %s', res)                 
            reg = dict()
            ad = dict()
            for poli in res: 
                ad['code'] = poli['code']
                ad['name'] = poli['name']
                _logger.info('\n******Cargando Fichero Tipos de Pólizas********\n')                                
                self.env['account.journal.types'].create(ad)
                _logger.info('\n******Fichero Cargado********\n')
            reg['modelo_id'] = 'Tipo de Pólizas'
            reg['actualizacion'] = fields.date.today()
            reg['creacion'] = fields.datetime.now()
            self.env['actua.registro'].create(reg)

        if self.sat_metodopago == True:
            
            data =  {
                                                       
                                     
                            "localizacion-mx":
                     { 
                     "Login":
                     { "rfc":rfc, "clave":clave
                     }, "Consulta":{ "Filtros":{ "fechadesde":"", "rangoinicial":"", "rangofinal":"", "paginar":"" } }} } 
                                
            headers =  {'content-type': 'application/json','timeout':'500000'}
            Respuesta =  requests.post(str(url) + "/c_metodosdepagoCE", data=json.dumps(data), headers=headers)
            res =  json.loads(Respuesta.content.decode("utf-8"))                   
            reg = dict()
            ad = dict()
            _logger.error('res: %s', res)
            for metodo in res: 
                ad['code'] = metodo['code'] 
                ad['name'] = metodo['name']                            
                self.env['eaccount.payment.methods'].create(ad)
                _logger.info('\n******Fichero Cargado********\n')
            reg['modelo_id'] = 'Metodo de Pagos CE'
            reg['actualizacion'] = fields.date.today()
            reg['creacion'] = fields.datetime.now()
            self.env['actua.registro'].create(reg)

        if self.sat_tipofactor == True:
            
            data = {
                                    
                            "localizacion-mx":
                     { 
                     "Login":
                     { "rfc":rfc, "clave":clave
                     }, "Consulta":{ "Filtros":{ "fechadesde":"", "rangoinicial":"", "rangofinal":"", "paginar":"" } }} } 
                         
            headers =  {'content-type': 'application/json','timeout':'500000'}
            Respuesta =  requests.post(str(url) + "/c_TipoFactor", data=json.dumps(data), headers=headers)
            res =  json.loads(Respuesta.content.decode("utf-8"))                   
            ad = dict()
            reg = dict()
            for factor in res:  
                ad["name"] = factor["TipoFactor"]
                self.env['sat.tipofactor'].create(ad)
                _logger.info('\n******Fichero Cargado********\n')
            reg['modelo_id'] = 'Tipos Factor'
            reg['actualizacion'] = fields.date.today()
            reg['creacion'] = fields.datetime.now()
            self.env['actua.registro'].create(reg)

        if self.sat_tipooperacion == True:
            
            data = {
                                    
                            "localizacion-mx":
                     { 
                     "Login":
                     { "rfc":rfc, "clave":clave
                     }, "Consulta":{ "Filtros":{ "fechadesde":"", "rangoinicial":"", "rangofinal":"", "paginar":"" } }} } 
                         
            headers =  {'content-type': 'application/json','timeout':'500000'}
            Respuesta =  requests.post(str(url) + "/c_TipoOperacion", data=json.dumps(data), headers=headers)
            res =  json.loads(Respuesta.content.decode("utf-8"))                   
            reg = dict()
            for factor in res:  
                
                self.env['sat.tipooperacion'].create(factor)
                _logger.info('\n******Fichero Cargado********\n')
            reg['modelo_id'] = 'Tipos de Operacion'
            reg['actualizacion'] = fields.date.today()
            reg['creacion'] = fields.datetime.now()
            self.env['actua.registro'].create(reg)

        if self.sat_traslado == True:
            
            data = {
                                    
                            "localizacion-mx":
                     { 
                     "Login":
                     { "rfc":rfc, "clave":clave
                     }, "Consulta":{ "Filtros":{ "fechadesde":"", "rangoinicial":"", "rangofinal":"", "paginar":"" } }} } 
                                          
                   
            headers =  {'content-type': 'application/json','timeout':'500000'}
            Respuesta =  requests.post(str(url) + "/c_MotivoTraslado", data=json.dumps(data), headers=headers)
            res =  json.loads(Respuesta.content.decode("utf-8"))                   
            reg = dict()
            for trasl in res:  
                
                self.env['sat.traslado'].create(trasl)
                _logger.info('\n******Fichero Cargado********\n')
            reg['modelo_id'] = 'Motivo Traslado'
            reg['actualizacion'] = fields.date.today()
            reg['creacion'] = fields.datetime.now()
            self.env['actua.registro'].create(reg)

        if self.sat_codigo_agrupador == True:
            
            data = {
                                      
                            "localizacion-mx":
                     { 
                     "Login":
                     { "rfc":rfc, "clave":clave
                     }, "Consulta":{ "Filtros":{ "fechadesde":"", "rangoinicial":"", "rangofinal":"", "paginar":"" } }} } 
                                           
            _logger.error('Datos enviados: %s', data)       
            headers =  {'content-type': 'application/json','timeout':'500000'}
            Respuesta =  requests.post(str(url) + "/c_CodigosAgrupadores", data=json.dumps(data), headers=headers)
            res =  json.loads(Respuesta.content.decode("utf-8"))                   
            _logger.error('data: %s ', res)
            reg = dict()
            ad = dict()
            for codigo in res: 
                _logger.info('\n******Cargando Fichero Codigo Agrupador Sat********\n')                                
                ad["key"] = codigo["Key"]
                ad["name"] = codigo["Name"]
                self.env['sat.account.code'].create(ad)
                _logger.info('\n******Fichero Cargado********\n') 
            reg['modelo_id'] = 'Codigos Agrupadores'
            reg['actualizacion'] = fields.date.today()
            reg['creacion'] = fields.datetime.now()
            self.env['actua.registro'].create(reg) 

        if self.sat_tasaocuota == True:
            
            data = {
                                                       
                      
                     "localizacion-mx":
                     { 
                     "Login":
                     { "rfc":rfc, "clave":clave
                     }, "Consulta":{ "Filtros":{ "fechadesde":"", "rangoinicial":"", "rangofinal":"", "paginar":"" } }} } 
                                            
                   

            headers =  {'content-type': 'application/json','timeout':'500000'}
            Respuesta =  requests.post(str(url) + "/c_TasaOCuota", data=json.dumps(data), headers=headers)
            res =  json.loads(Respuesta.content.decode("utf-8"))                  
            _logger.error('data: %s ', res)
            ad = dict()
            reg = dict()
            for tasa in res: 
                ad['name'] = tasa['RangoOFijo']
                ad['value_min'] = tasa['ValorMinimo']
                ad['value_max'] = tasa['ValorMaximo']
                ad['taxes'] = tasa['Impuesto']
                ad['factor'] = tasa['Factor']
                ad['retencion'] = tasa['Retencion']
                ad['traslado'] = tasa['Traslado']
                #ad['fecha_start'] = tasa['FechaInicioVigencia']                             
                self.env['sat.tasa.cuota'].create(ad)
                _logger.info('\n******Fichero Cargado********\n')
            reg['modelo_id'] = 'Tasa o Cuota'
            reg['actualizacion'] = fields.date.today()
            reg['creacion'] = fields.datetime.now()
            self.env['actua.registro'].create(reg)

        if self.sat_clavepedemiento == True:
            
            data = {
                                                       
                      
                     "localizacion-mx":
                     { 
                     "Login":
                     { "rfc":rfc, "clave":clave
                     }, "Consulta":{ "Filtros":{ "fechadesde":"", "rangoinicial":"", "rangofinal":"", "paginar":"" } }} } 
                                            
                   

            headers =  {'content-type': 'application/json','timeout':'500000'}
            Respuesta =  requests.post(str(url) + "/c_ClavePedimento", data=json.dumps(data), headers=headers)
            res =  json.loads(Respuesta.content.decode("utf-8"))                  
            _logger.error('data: %s ', res)
            reg = dict()

            for clave in res: 
                                        
                self.env['sat.clavepedimento'].create(clave)
                _logger.info('\n******Fichero Cargado********\n')
            reg['modelo_id'] = 'Claves Pedimentos'
            reg['actualizacion'] = fields.date.today()
            reg['creacion'] = fields.datetime.now()
            self.env['actua.registro'].create(reg)

        if self.pacs == True:
            
            data = {
                                                       
                      
                     "localizacion-mx":
                     { 
                     "Login":
                     { "rfc":rfc, "clave":clave
                     }, "Consulta":{ "Filtros":{ "fechadesde":"", "rangoinicial":"", "rangofinal":"", "paginar":"" } }} } 
                                            
                   

            headers =  {'content-type': 'application/json','timeout':'500000'}
            Respuesta =  requests.post(str(url) + "/CTE_PAC", data=json.dumps(data), headers=headers)
            res =  json.loads(Respuesta.content.decode("utf-8"))                  
            _logger.error('data: %s ', res)
            ad = dict()
            reg = dict()
            for pac in res: 
                ad['name'] = pac['PacID']
                ad['nombre_pac'] = pac['NombrePac']                                        
                self.env['pac.timbres'].create(ad)
                _logger.info('\n******Fichero Cargado********\n')
            reg['modelo_id'] = 'PACS'
            reg['actualizacion'] = fields.date.today()
            reg['creacion'] = fields.datetime.now()
            self.env['actua.registro'].create(reg)

        if self.sat_meses == True:            
            data = {
                                    
                            "localizacion-mx":
                     { 
                     "Login":
                     { "rfc":rfc, "clave":clave
                     }, "Consulta":{ "Filtros":{ "fechadesde":"", "rangoinicial":"", "rangofinal":"", "paginar":"" }  } } } 
                         
            _logger.error('data: %s ', data)
            headers =  {'content-type': 'application/json','timeout':'500000'}
            Respuesta =  requests.post(str(url) + "/c_meses", data=json.dumps(data), headers=headers)                
            mese =  json.loads(Respuesta.content.decode("utf-8"))
            _logger.error('meses: %s', mese)
            reg = dict()            
            for mes in mese:                                         
                self.env['sat.meses'].create(mes)
                _logger.info('\n******Fichero Cargado********\n')
            reg['modelo_id'] = 'Meses'
            reg['actualizacion'] = fields.date.today()
            reg['creacion'] = fields.datetime.now()
            self.env['actua.registro'].create(reg)        
        

        if self.sat_periodicidad == True:
            
            data = {
                                    
                            "localizacion-mx":
                     { 
                     "Login":
                     { "rfc":rfc, "clave":clave
                     }, "Consulta":{ "Filtros":{ "fechadesde":"", "rangoinicial":"", "rangofinal":"", "paginar":"" } }} }
                       
            _logger.error('data: %s ', data)
            headers =  {'content-type': 'application/json','timeout':'500000'}
            Respuesta =  requests.post(str(url) + "/c_periodicidad", data=json.dumps(data), headers=headers)
            res =  json.loads(Respuesta.content.decode("utf-8"))                  
            _logger.error('data: %s ', res)
            reg = dict()          
            for periodicidad in res:                                                           
                self.env['sat.periodicidad'].create(periodicidad)
                _logger.info('\n******Fichero Cargado********\n')
            reg['modelo_id'] = 'Periodicidad'
            reg['actualizacion'] = fields.date.today()
            reg['creacion'] = fields.datetime.now()
            self.env['actua.registro'].create(reg)        
        
        if self.sat_objetoimp == True:
            
            data = {
                                    
                            "localizacion-mx":
                     { 
                     "Login":
                     { "rfc":rfc, "clave":clave
                     }, "Consulta":{ "Filtros":{ "fechadesde":"", "rangoinicial":"", "rangofinal":"", "paginar":"" } }} }
            
            headers =  {'content-type': 'application/json','timeout':'500000'}
            Respuesta =  requests.post(str(url) + "/c_Objetoimp", data=json.dumps(data), headers=headers)
            _logger.error('respuesta: %s', Respuesta)
            res =  json.loads(Respuesta.content.decode("utf-8"))
            _logger.error('respuesta: %s', res)             
            reg = dict()
            ad = dict()
            for objetoimp in res:
                                                                         
                self.env['sat.objetoimp'].create(objetoimp)
                _logger.info('\n******Fichero Cargado********\n')
            reg['modelo_id'] = 'ObjetoImp'
            reg['actualizacion'] = fields.date.today()
            reg['creacion'] = fields.datetime.now()
            self.env['actua.registro'].create(reg)
        
        if self.sat_exportacion == True:
            
            data = {
                                    
                            "localizacion-mx":
                     { 
                     "Login":
                     { "rfc":rfc, "clave":clave
                     }, "Consulta":{ "Filtros":{ "fechadesde":"", "rangoinicial":"", "rangofinal":"", "paginar":"" } }} } 
                         
            headers =  {'content-type': 'application/json','timeout':'500000'}
            Respuesta =  requests.post(str(url) + "/c_Exportacion", data=json.dumps(data), headers=headers)
            res =  json.loads(Respuesta.content.decode("utf-8"))                 
            reg = dict()
            for exportacion in res: 
                                                        
                self.env['sat.exportacion'].create(exportacion)
                _logger.info('\n******Fichero Cargado********\n')
            reg['modelo_id'] = 'Exportación'
            reg['actualizacion'] = fields.date.today()
            reg['creacion'] = fields.datetime.now()
            self.env['actua.registro'].create(reg)


        _logger.info('\n******Fin de la carga de Datos********\n')   
        return self._reopen_wizard()

    @api.model
    def actualiza_catalogos(self):
        webservice_url = self.env['ir.config_parameter'].sudo().get_param('webservice.url')       
        rfc = self.env['ir.config_parameter'].sudo().get_param('webservice.rfc_web')
        clave = self.env['ir.config_parameter'].sudo().get_param('webservice.password')
        if webservice_url == 'test':
            url = self.env['ir.config_parameter'].sudo().get_param('webservice.url_name_prue')
        if webservice_url == 'product':
            url = self.env['ir.config_parameter'].sudo().get_param('webservice.url_name_produc')
        if not rfc or not clave or not url: 
            raise UserError(_("Error!\nlos Datos de conexión al webservice son incorrectos o estan vacios .\n\n" 'RFC: %s\n' 'Clave: %s\n' 'URL: %s\n') % (rfc, clave, url))
              
        if self.sat_aduana == True:
            registro = self.env['actua.registro'].search([('modelo_id', '=', 'Aduanas')])
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
            aduanas =  json.loads(Respuesta.content.decode("utf-8"))
            _logger.error('Respuestas: %s', aduanas)
            for aduana in aduanas: 
                _logger.info('\n******Actualización de Fichero Aduanas********\n')
                aduanas_sat = self.env['sat.aduana'].search([('code', '=', aduana['code'])])

                if aduanas_sat:
                    aduanas_sat.write(aduana)  

                else:
                    aduanas_sat.create(aduana)                           
                
                _logger.info('\n******Fichero Actualizado********\n')
            registro.actualizacion = fields.date.today()


        if self.sat_producto == True:
            registro = self.env['actua.registro'].search([('modelo_id', '=', 'Productos')])
            fecha_actu = datetime.datetime.strptime(str(registro.actualizacion), '%Y-%m-%d')
            fecha_actua = fecha_actu.strftime('%d-%m-%Y')   
                        
            data = {
                                    
                            "localizacion-mx":
                     { 
                     "Login":
                     { "rfc":rfc, "clave":clave
                     }, "Consulta":{ "Filtros":{ "fechadesde": fecha_actua, "rangoinicial":"", "rangofinal":"", "paginar":"" } }}}
            _logger.error("Datos: %s", data)
            headers =  {'content-type': 'application/json','timeout':'500000'}
            Respuesta =  requests.post(str(url) + "/c_ClaveProdServ", data=json.dumps(data), headers=headers)
            res =  json.loads(Respuesta.content.decode("utf-8"))                  
            _logger.error('PRoductos: %s', res)
            for product in res:   
                productos = self.env['sat.producto'].search([('code','=', product['code'])])   
                if productos:
                    productos.write(product) 
                else:
                    productos.create(product)
                _logger.info('\n******Fichero Actualizado********\n')
            registro.actualizacion = fields.date.today()
        

        if self.sat_paises == True:
            registro = self.env['actua.registro'].search([('modelo_id', '=', 'Paises')])
            fecha_actu = datetime.datetime.strptime(str(registro.actualizacion), '%Y-%m-%d')
            fecha_actua = fecha_actu.strftime('%d-%m-%Y')

            data = {
                                    
                            "localizacion-mx":
                     { 
                     "Login":
                     { "rfc":rfc, "clave":clave
                     }, "Consulta":{ "Filtros":{ "fechadesde": fecha_actua, "rangoinicial":"", "rangofinal":"", "paginar":"" } }} }
                       
            _logger.error('data: %s ', data)
            headers =  {'content-type': 'application/json','timeout':'500000'}
            Respuesta =  requests.post(str(url) + "/c_Pais", data=json.dumps(data), headers=headers)
            res =  json.loads(Respuesta.content.decode("utf-8"))                  
            _logger.error('data: %s ', res)
            for pais in res: 
                _logger.info('\n******Actualizando Fichero Paises********\n')
                paises = self.env['res.country.sat.code'].search([('code', '=', pais['code'])])
                if paises:
                    paises.write(pais)
                else:
                    paises.create(pais)
                _logger.info('\n******Fichero Actualizado********\n')        
            registro.actualizacion = fields.date.today()
            
        if self.sat_colonia == True:
            registro = self.env['actua.registro'].search([('modelo_id', '=', 'Colonias')])
            fecha_actu = datetime.datetime.strptime(str(registro.actualizacion), '%Y-%m-%d')
            fecha_actua = fecha_actu.strftime('%d-%m-%Y')

            data = {"localizacion-mx":{"login":{"rfc":rfc,"clave":clave},
                "Consulta":{"Filtros":{"fechadesde":fecha_actua,"rangoinicial":"","rangofinal":"","paginar":""}}}}
            _logger.error('Colonias: %s', data)
            headers =  {'content-type': 'application/json','timeout':'500000'}
            Respuesta =  requests.post(str(url) + "/c_Colonia", data=json.dumps(data), headers=headers)
            res =  json.loads(Respuesta.content.decode("utf-8"))                 
            _logger.error('Colonias: %s', res)
            for col in res:
                colonias = self.env['res.colonia.zip.sat.code'].search([('code', '=', col['code'])])
                if colonias:
                    colonias.write(col)
                else:
                    colonias.create(col)
                _logger.info('\n******Fichero Actualizado********\n')
            registro.actualizacion = fields.date.today()
            
        if self.sat_codigo_postal == True:
            registro = self.env['actua.registro'].search([('modelo_id', '=', 'Códigos Postales')])
            fecha_actu = datetime.datetime.strptime(str(registro.actualizacion), '%Y-%m-%d')
            fecha_actua = fecha_actu.strftime('%d-%m-%Y')

            data = {
                                    
                            "localizacion-mx":
                     { 
                     "Login":
                     { "rfc":rfc, "clave":clave
                     }, "Consulta":{ "Filtros":{ "fechadesde":fecha_actua, "rangoinicial":"", "rangofinal":"", "paginar":"" }}}} 
            _logger.error("Datos: %s", data)         
            headers =  {'content-type': 'application/json','timeout':'500000'}
            Respuesta =  requests.post(str(url) + "/c_CodigoPostal", data=json.dumps(data), headers=headers)
            res =  json.loads(Respuesta.content.decode("utf-8"))
            _logger.error('Codigo postal: %s', res) 
            for cp in res: 
                codigo_postal = self.env['res.country.zip.sat.code'].search([('code', '=', cp['code'])])
                if codigo_postal:
                    codigo_postal.write(cp)
                else:
                    codigo_postal.create(cp)
                _logger.info('\n******Fichero Actualizado********\n')
            registro.actualizacion = fields.date.today()
            
        
        if self.sat_localidad == True:
            registro = self.env['actua.registro'].search([('modelo_id', '=', 'Localidades')])
            fecha_actu = datetime.datetime.strptime(str(registro.actualizacion), '%Y-%m-%d')
            fecha_actua = fecha_actu.strftime('%d-%m-%Y')

            data = {
                                    
                            "localizacion-mx":
                     { 
                     "Login":
                     { "rfc":rfc, "clave":clave
                     }, "Consulta":{ "Filtros":{ "fechadesde":fecha_actua, "rangoinicial":"", "rangofinal":"", "paginar":"" } }} }
                       
            headers =  {'content-type': 'application/json','timeout':'500000'}
            Respuesta =  requests.post(str(url) + "/c_Localidad", data=json.dumps(data), headers=headers)
            res =  json.loads(Respuesta.content.decode("utf-8"))                 
        
            for localidad in res: 
                _logger.info('\n******Actualizando Fichero Localidades********\n')
                localidades = self.env['res.country.locality.sat.code'].search([('code', '=', localidad['code'])])                                          
                if localidades:
                    localidades.write(localidad)
                else:
                    localidades.create(localidad)
                _logger.info('\n******Fichero Actualizado********\n')
            registro.actualizacion = fields.date.today()

        if self.sat_estados == True:
            registro = self.env['actua.registro'].search([('modelo_id', '=', 'Estados')])
            fecha_actu = datetime.datetime.strptime(str(registro.actualizacion), '%Y-%m-%d')
            fecha_actua = fecha_actu.strftime('%d-%m-%Y')

            data = {
                                    
                            "localizacion-mx":
                     { 
                     "Login":
                     { "rfc":rfc, "clave":clave
                     }, "Consulta":{ "Filtros":{ "fechadesde":fecha_actua, "rangoinicial":"", "rangofinal":"", "paginar":"" } }} } 
                         
            headers =  {'content-type': 'application/json','timeout':'500000'}
            Respuesta =  requests.post(str(url) + "/c_Estado", data=json.dumps(data), headers=headers)
            res =  json.loads(Respuesta.content.decode("utf-8"))                 
        
            for estados in res: 
                _logger.info('\n******Actualizando Fichero Estados********\n') 
                estados_sat = self.env['res.country.state.sat.code'].search([('code', '=', estados['code'])])
                if estados_sat:
                    estados_sat.write()
                else:
                    estados_sat.create(estados)
                _logger.info('\n******Fichero Actualizado********\n')
            registro.actualizacion = fields.date.today()
        

        if self.sat_municipio == True:
            registro = self.env['actua.registro'].search([('modelo_id', '=', 'Municipios')])
            fecha_actu = datetime.datetime.strptime(str(registro.actualizacion), '%Y-%m-%d')
            fecha_actua = fecha_actu.strftime('%d-%m-%Y')

            data = {
                                    
                            "localizacion-mx":
                     { 
                     "Login":
                     { "rfc":rfc, "clave":clave
                     }, "Consulta":{ "Filtros":{ "fechadesde":fecha_actua, "rangoinicial":"", "rangofinal":"", "paginar":"" } }} }
                         
            headers =  {'content-type': 'application/json','timeout':'500000'}
            Respuesta =  requests.post(str(url) + "/c_Municipio", data=json.dumps(data), headers=headers)
            res =  json.loads(Respuesta.content.decode("utf-8"))                  
        
            for munip in res: 
                _logger.info('\n******Actualizando Fichero Municipios********\n')  
                municipios = self.env['res.country.township.sat.code'].search([('code', '=', munip['code'])])
                if municipios:
                    municipos.write(munip)
                else:
                    municipos.create(munip)
                _logger.info('\n******Fichero Actualizado********\n')
            registro.actualizacion = fields.date.today()

        if self.sat_udm == True:
            registro = self.env['actua.registro'].search([('modelo_id', '=', 'Unidades de Medida')])
            fecha_actu = datetime.datetime.strptime(str(registro.actualizacion), '%Y-%m-%d')
            fecha_actua = fecha_actu.strftime('%d-%m-%Y')

            data = {
                                    
                            "localizacion-mx":
                     { 
                     "Login":
                     { "rfc":rfc, "clave":clave
                     }, "Consulta":{ "Filtros":{ "fechadesde":fecha_actua, "rangoinicial":"", "rangofinal":"", "paginar":"" } } } } 
                         
            headers = {'content-type': 'application/json','timeout':'500000'}
            Respuesta =  requests.post(str(url) + "/c_ClaveUnidad", data=json.dumps(data), headers=headers)
            res =  json.loads(Respuesta.content.decode("utf-8"))                   
        
            for um in res: 
                _logger.info('\n******Actualizando Fichero Unidades de Medida********\n')
                uom = self.env['sat.udm'].search([('code', '=', um['code'])])
                if uom:
                    uom.write(um)
                else:
                    uom.create(um)
                _logger.info('\n******Fichero Actualizado********\n')
            registro.actualizacion = fields.date.today()

        if self.sat_uso_cfdi == True:
            registro = self.env['actua.registro'].search([('modelo_id', '=', 'Uso de CFDI')])
            fecha_actu = datetime.datetime.strptime(str(registro.actualizacion), '%Y-%m-%d')
            fecha_actua = fecha_actu.strftime('%d-%m-%Y')

            data = {
                                    
                            "localizacion-mx":
                     { 
                     "Login":
                     { "rfc":rfc, "clave":clave
                     }, "Consulta":{ "Filtros":{ "fechadesde":fecha_actua, "rangoinicial":"", "rangofinal":"", "paginar":"" } }} } 
                                          
                   
            headers =  {'content-type': 'application/json','timeout':'500000'}
            Respuesta =  requests.post(str(url) + "/c_UsoCFDI", data=json.dumps(data), headers=headers)
            res =  json.loads(Respuesta.content.decode("utf-8"))                  
        
            for cfdi in res: 
                _logger.info('\n******Actualizando Fichero Uso Cfdi********\n')  
                uso_cfdi = self.env['sat.uso.cfdi'].search([('code', '=', cfdi['code'])])
                if uso_cfdi:
                    uso_cfdi.write(cfdi)
                else:
                   uso_cfdi.create(cfdi)
                _logger.info('\n******Fichero Actualizado********\n')
            registro.actualizacion = fields.date.today()

        if self.sat_pedimento == True:            
            registro = self.env['actua.registro'].search([('modelo_id', '=', 'Pedimentos')])
            fecha_actu = datetime.datetime.strptime(str(registro.actualizacion), '%Y-%m-%d')
            fecha_actua = fecha_actu.strftime('%d-%m-%Y')

            data = {
                                    
                            "localizacion-mx":
                     { 
                     "Login":
                     { "rfc":rfc, "clave":clave
                     }, "Consulta":{ "Filtros":{ "fechadesde":fecha_actua, "rangoinicial":"", "rangofinal":"", "paginar":"" } } } } 
                        
            headers =  {'content-type': 'application/json','timeout':'500000'}
            Respuesta =  requests.post(str(url) + "/c_PedimentoAduanal", data=json.dumps(data), headers=headers)
            res =  json.loads(Respuesta.content.decode("utf-8"))                   
            _logger.error('Respuesta: %s', res)
            ad = dict()    
            for patente in res: 
                patentes = self.env['sat.patente'].search([('name_1', '=', patente['name'])])
                if patentes:                    
                    ad['name_1'] = patente['name']
                    ad['cantidad'] = patente['Cantidad']
                    ad['ejercicio'] = patente['ejercicio']
                    ad['start_date'] = patente['start_date']          
                    ad['aduana_code'] = patente['c_PedimentoAduanalID'] 
                    patentes.write(ad)
                else:
                    ad['name_1'] = patente['name']
                    ad['cantidad'] = patente['Cantidad']
                    ad['ejercicio'] = patente['ejercicio']
                    ad['start_date'] = patente['start_date']          
                    ad['aduana_code'] = patente['c_PedimentoAduanalID']                
                    patentes.create(ad)
                _logger.info('\n******Fichero Actualizado********\n')
            registro.actualizacion = fields.date.today()

        if self.sat_arancel == True:
            registro = self.env['actua.registro'].search([('modelo_id', '=', 'Aranceles')])
            fecha_actu = datetime.datetime.strptime(str(registro.actualizacion), '%Y-%m-%d')
            fecha_actua = fecha_actu.strftime('%d-%m-%Y')

            data = {
                                    
                            "localizacion-mx":
                     { 
                     "Login":
                     { "rfc":rfc, "clave":clave
                     }, "Consulta":{ "Filtros":{ "fechadesde":fecha_actua, "rangoinicial":"", "rangofinal":"", "paginar":"" } } } } 
                         
            headers =  {'content-type': 'application/json','timeout':'500000'}
            Respuesta =  requests.post(str(url) + "/c_FraccionArancelaria", data=json.dumps(data), headers=headers)
            res =  json.loads(Respuesta.content.decode("utf-8"))                  
        
            for arancel in res: 
                _logger.info('\n******Actualizando Fichero Aranceles********\n')
                aranceles = self.env['sat.arancel'].search([('code', '=', arancel['code'])]) 
                if aranceles:
                    aranceles.write(arancel)  
                else:
                    arancel.create(arancel)
                _logger.info('\n******Fichero Actualizado********\n')
            registro.actualizacion = fields.date.today()
        if self.sat_bancos == True:
            registro = self.env['actua.registro'].search([('modelo_id', '=', 'Bancos')])
            fecha_actu = datetime.datetime.strptime(str(registro.actualizacion), '%Y-%m-%d')
            fecha_actua = fecha_actu.strftime('%d-%m-%Y')

            data = {
                                    
                            "localizacion-mx":
                     { 
                     "Login":
                     { "rfc":rfc, "clave":clave
                     }, "Consulta":{ "Filtros":{ "fechadesde":fecha_actua, "rangoinicial":"", "rangofinal":"", "paginar":"" } } } } 
            _logger.error("Data: %s", data)            
            headers =  {'content-type': 'application/json','timeout':'500000'}
            Respuesta =  requests.post(str(url) + "/c_Banco", data=json.dumps(data), headers=headers)
            res =  json.loads(Respuesta.content.decode("utf-8"))               
            _logger.error('Respuesta: %s', res)
            
            for bancos in res: 
                _logger.info('\n******Actualizando Fichero Bancos********\n')
                banco = self.env['eaccount.bank'].search([('bic', '=', bancos['bic'])])
                if banco:
                    banco.write(bancos)
                else:
                    banco.create(bancos)
                    #_logger.error('Resultados: %s', ad)
                _logger.info('\n******Fichero Actualizado********\n')
            registro.actualizacion = fields.date.today()

        if self.sat_regimen_fiscal == True:
            registro = self.env['actua.registro'].search([('modelo_id', '=', 'Regimen Fiscal')])
            fecha_actu = datetime.datetime.strptime(str(registro.actualizacion), '%Y-%m-%d')
            fecha_actua = fecha_actu.strftime('%d-%m-%Y')

            data = {
                                    
                            "localizacion-mx":
                     { 
                     "Login":
                     { "rfc":rfc, "clave":clave
                     }, "Consulta":{ "Filtros":{ "fechadesde":fecha_actua, "rangoinicial":"", "rangofinal":"", "paginar":"" } }} } 
                        
            headers =  {'content-type': 'application/json','timeout':'500000'}
            Respuesta =  requests.post(str(url) + "/c_RegimenFiscal", data=json.dumps(data), headers=headers)
            res =  json.loads(Respuesta.content.decode("utf-8"))                   
            _logger.error('Respuesta: %s', res)
            for rg in res: 
                _logger.info('\n******Actualizando Fichero Regimen Fiscal********\n')  
                regimen = self.env['sat.regimen.fiscal'].search([('code', '=', rg['code'])]) 
                if regimen:
                    regimen.write(rg) 
                else:

                    regimen.create(rg)
                _logger.info('\n******Fichero Actualizado********\n')
            registro.actualizacion = fields.date.today()

        if self.sat_impuestos == True:
            registro = self.env['actua.registro'].search([('modelo_id', '=', 'Impuestos')])
            fecha_actu = datetime.datetime.strptime(str(registro.actualizacion), '%Y-%m-%d')
            fecha_actua = fecha_actu.strftime('%d-%m-%Y')

            data = {
                                    
                            "localizacion-mx":
                     { 
                     "Login":
                     { "rfc":rfc, "clave":clave
                     }, "Consulta":{ "Filtros":{ "fechadesde":fecha_actua, "rangoinicial":"", "rangofinal":"", "paginar":"" } }} } 
                         
            headers =  {'content-type': 'application/json','timeout':'500000'}
            Respuesta =  requests.post(str(url) + "/c_Impuesto", data=json.dumps(data), headers=headers)
            res =  json.loads(Respuesta.content.decode("utf-8"))                  
                
            for impu in res: 
                _logger.info('\n******Cargando Fichero Impuestos********\n') 
                impuestos = self.env['sat.impuesto'].search([('code', '=', impu['code'])]) 
                if impuestos:
                    impuestos.write(impu)
                else:             
                    impuestos.create(impu)
                _logger.info('\n******Fichero Cargado********\n')
            registro.actualizacion = fields.date.today()

        if self.sat_formas_pago == True:
            registro = self.env['actua.registro'].search([('modelo_id', '=', 'Formas de Pago')])
            fecha_actu = datetime.datetime.strptime(str(registro.actualizacion), '%Y-%m-%d')
            fecha_actua = fecha_actu.strftime('%d-%m-%Y')

            data = {
                                    
                            "localizacion-mx":
                     { 
                     "Login":
                     { "rfc":rfc, "clave":clave
                     }, "Consulta":{ "Filtros":{ "fechadesde":fecha_actua, "rangoinicial":"", "rangofinal":"", "paginar":"" } }} } 
                        
            headers =  {'content-type': 'application/json','timeout':'500000'}
            Respuesta =  requests.post(str(url) + "/c_FormaPago", data=json.dumps(data), headers=headers)
            res =  json.loads(Respuesta.content.decode("utf-8"))                   
        
            for formas in res: 
                _logger.info('\n******Cargando Fichero Formas de Pago********\n')  
                formas_pago = self.env['pay.method'].search([('code', '=', formas['code'])])
                if formas_pago:
                    formas_pago.write(formas)  
                else:

                    formas_pago.create(formas)
                _logger.info('\n******Fichero Cargado********\n')
            registro.actualizacion = fields.date.today()

        if self.sat_metodo_pago == True:
            registro = self.env['actua.registro'].search([('modelo_id', '=', 'Metodos de Pagos')])
            fecha_actu = datetime.datetime.strptime(str(registro.actualizacion), '%Y-%m-%d')
            fecha_actua = fecha_actu.strftime('%d-%m-%Y')

            data = {
                                    
                            "localizacion-mx":
                     { 
                     "Login":
                     { "rfc":rfc, "clave":clave
                     }, "Consulta":{ "Filtros":{ "fechadesde":fecha_actua, "rangoinicial":"", "rangofinal":"", "paginar":"" } }} } 
                        
            headers =  {'content-type': 'application/json','timeout':'500000'}
            Respuesta =  requests.post(str(url) + "/c_MetodoPago", data=json.dumps(data), headers=headers)
            res =  json.loads(Respuesta.content.decode("utf-8"))                   
        
            for mp in res: 
                _logger.info('\n******Cargando Fichero Método de Pago********\n')  
                metod_pago = self.env['sat.metodo.pago'].search([('code', '=', mp['code'])])
                if metod_pago:
                    metod_pago.write(mp)
                else:
                    metod_pago.create(mp)
                _logger.info('\n******Fichero Cargado********\n')
            registro.actualizacion = fields.date.today()

        if self.sat_tipos_relacion == True:
            registro = self.env['actua.registro'].search([('modelo_id', '=', 'Tipos Relacion CFDI')])
            fecha_actu = datetime.datetime.strptime(str(registro.actualizacion), '%Y-%m-%d')
            fecha_actua = fecha_actu.strftime('%d-%m-%Y')

            data = {
                                    
                            "localizacion-mx":
                     { 
                     "Login":
                     { "rfc":rfc, "clave":clave
                     }, "Consulta":{ "Filtros":{ "fechadesde":fecha_actua, "rangoinicial":"", "rangofinal":"", "paginar":"" } }} } 
                         
            headers =  {'content-type': 'application/json','timeout':'500000'}
            Respuesta =  requests.post(str(url) + "/c_TipoRelacion", data=json.dumps(data), headers=headers)
            res =  json.loads(Respuesta.content.decode("utf-8"))                   
        
            for tipos in res: 
                _logger.info('\n******Cargando Fichero Tipos de Relacion********\n')
                tipo_relacion = self.env['sat.tipo.relacion.cfdi'].search([('code', '=', tipos['code'])])                
                if tipo_relacion:
                    tipo_relacion.write(tipos)
                else:
                    tipo_relacion.create(tipos)
                _logger.info('\n******Fichero Cargado********\n')
            registro.actualizacion = fields.date.today()

        if self.sat_patentes_aduanales == True:
            registro = self.env['actua.registro'].search([('modelo_id', '=', 'Patentes Aduanales')])
            fecha_actu = datetime.datetime.strptime(str(registro.actualizacion), '%Y-%m-%d')
            fecha_actua = fecha_actu.strftime('%d-%m-%Y')

            data = {
                                    
                            "localizacion-mx":
                     { 
                     "Login":
                     { "rfc":rfc, "clave":clave
                     }, "Consulta":{ "Filtros":{ "fechadesde":fecha_actua, "rangoinicial":"", "rangofinal":"", "paginar":"" } }} } 
                         
            headers =  {'content-type': 'application/json','timeout':'500000'}
            Respuesta =  requests.post(str(url) + "/c_PatenteAduanal", data=json.dumps(data), headers=headers)
            res =  json.loads(Respuesta.content.decode("utf-8"))                   
            
            ad = dict()
            for tipos in res: 
                _logger.info('\n******Cargando Fichero Patentes Aduanales********\n')  
                patente_aduana = self.env['sat.patente.aduanal'].search([('code', '=', tipos['code'])])              
                
                if patente_aduana:
                    ad["code"] = tipos["code"]
                    patente_aduana.write(ad)
                else:
                    ad["code"] = tipos["code"]
                    patente_aduana.create(ad)
                _logger.info('\n******Fichero Cargado********\n')
            registro.actualizacion = fields.date.today()

        if self.sat_moneda == True:
            registro = self.env['actua.registro'].search([('modelo_id', '=', 'Monedas')])
            fecha_actu = datetime.datetime.strptime(str(registro.actualizacion), '%Y-%m-%d')
            fecha_actua = fecha_actu.strftime('%d-%m-%Y')

            data = {
                                    
                            "localizacion-mx":
                     { 
                     "Login":
                     { "rfc":rfc, "clave":clave
                     }, "Consulta":{ "Filtros":{ "fechadesde":fecha_actua, "rangoinicial":"", "rangofinal":"", "paginar":"" } }} } 
                         

            headers =  {'content-type': 'application/json','timeout':'500000'}
            Respuesta =  requests.post(str(url) + "/c_Moneda", data=json.dumps(data), headers=headers)
            res =  json.loads(Respuesta.content.decode("utf-8"))                  
            _logger.error('data: %s ', res)
            for tipos in res: 
                _logger.info('\n******Cargando Fichero Monedas********\n') 
                monedas = self.env['eaccount.currency'].search([('code', '=', tipos['code'])])
                if monedas:
                    monedas.write(tipos)
                else:
                    monedas.create(tipos)
                _logger.info('\n******Fichero Cargado********\n')
            registro.actualizacion = fields.date.today()

        if self.sat_tipo_comprobante == True:
            registro = self.env['actua.registro'].search([('modelo_id', '=', 'Tipo de Comprobante')])
            fecha_actu = datetime.datetime.strptime(str(registro.actualizacion), '%Y-%m-%d')
            fecha_actua = fecha_actu.strftime('%d-%m-%Y')

            data = {
                                    
                            "localizacion-mx":
                     { 
                     "Login":
                     { "rfc":rfc, "clave":clave
                     }, "Consulta":{ "Filtros":{ "fechadesde":fecha_actua, "rangoinicial":"", "rangofinal":"", "paginar":"" } }} } 
                         
            headers =  {'content-type': 'application/json','timeout':'500000'}
            Respuesta =  requests.post(str(url) + "/c_TipoComprobante", data=json.dumps(data), headers=headers)
            res =  json.loads(Respuesta.content.decode("utf-8"))                   
        
            for compro in res: 
                _logger.info('\n******Cargando Fichero Tipos de Comprobante********\n')  
                tipo_comprobante = self.env['sat.tipo.comprobante'].search([('code', '=', compro['code'])])
                if tipo_comprobante:
                    tipo_comprobante.write(compro)
                else:
                    tipo_comprobante.create(compro)
                _logger.info('\n******Fichero Cargado********\n')
            registro.actualizacion = fields.date.today()

        if self.tipo_poliza == True:
            registro = self.env['actua.registro'].search([('modelo_id', '=', 'Tipo de Pólizas')])
            fecha_actu = datetime.datetime.strptime(str(registro.actualizacion), '%Y-%m-%d')
            fecha_actua = fecha_actu.strftime('%d-%m-%Y')

            data =  {
                                                       
                                     
                            "localizacion-mx":
                     { 
                     "Login":
                     { "rfc":rfc, "clave":clave
                     }, "Consulta":{ "Filtros":{ "fechadesde":fecha_actua, "rangoinicial":"", "rangofinal":"", "paginar":"" } }} } 
                                   
            headers =  {'content-type': 'application/json','timeout':'500000'}
            Respuesta =  requests.post(str(url) + "/c_tiposdepolizas", data=json.dumps(data), headers=headers)
            res =  json.loads(Respuesta.content.decode("utf-8"))                   
        
            for poli in res: 
                _logger.info('\n******Cargando Fichero Tipos de Pólizas********\n') 
                polizas = self.env['account.journal.types'].search([('code', '=', poli['code'])])
                if polizas:
                    polizas.write(poli)
                else:
                    polizas.create(poli)
                _logger.info('\n******Fichero Cargado********\n')
            registro.actualizacion = fields.date.today()

        if self.sat_metodopago == True:
            registro = self.env['actua.registro'].search([('modelo_id', '=', 'Metodo de Pagos CE')])
            fecha_actu = datetime.datetime.strptime(str(registro.actualizacion), '%Y-%m-%d')
            fecha_actua = fecha_actu.strftime('%d-%m-%Y')

            data =  {
                                                       
                                     
                            "localizacion-mx":
                     { 
                     "Login":
                     { "rfc":rfc, "clave":clave
                     }, "Consulta":{ "Filtros":{ "fechadesde":fecha_actua, "rangoinicial":"", "rangofinal":"", "paginar":"" } }} } 
                                
            headers =  {'content-type': 'application/json','timeout':'500000'}
            Respuesta =  requests.post(str(url) + "/c_metodosdepagoCE", data=json.dumps(data), headers=headers)
            res =  json.loads(Respuesta.content.decode("utf-8"))                   
        
            for metodo in res: 
                metodo_pago = self.env['eaccount.payment.methods'].search([('code', '=', metodo['code'])])
                if metodo_pago:
                    metodo_pago.write(metodo)
                else:
                    metodo_pago.create(metodo)
                _logger.info('\n******Fichero Cargado********\n')
            registro.actualizacion = fields.date.today()

        if self.sat_tipofactor == True:
            registro = self.env['actua.registro'].search([('modelo_id', '=', 'Tipos Factor')])
            fecha_actu = datetime.datetime.strptime(str(registro.actualizacion), '%Y-%m-%d')
            fecha_actua = fecha_actu.strftime('%d-%m-%Y')

            data = {
                                    
                            "localizacion-mx":
                     { 
                     "Login":
                     { "rfc":rfc, "clave":clave
                     }, "Consulta":{ "Filtros":{ "fechadesde":fecha_actua, "rangoinicial":"", "rangofinal":"", "paginar":"" } }} } 
                         
            headers =  {'content-type': 'application/json','timeout':'500000'}
            Respuesta =  requests.post(str(url) + "/c_TipoFactor", data=json.dumps(data), headers=headers)
            res =  json.loads(Respuesta.content.decode("utf-8"))                   
            ad = dict()
            for factor in res:  
                ad["name"] = factor["TipoFactor"]
                tipo_factor = self.env['sat.tipofactor'].search([('name', '=', factor['name'])])
                if tipo_factor:
                    tipo_factor.write(ad)
                else:
                    tipo_factor.create(ad)
                _logger.info('\n******Fichero Actualizado********\n')
            registro.actualizacion = fields.date.today()

        if self.sat_tipooperacion == True:
            registro = self.env['actua.registro'].search([('modelo_id', '=', 'Tipos de Operacion')])
            fecha_actu = datetime.datetime.strptime(str(registro.actualizacion), '%Y-%m-%d')
            fecha_actua = fecha_actu.strftime('%d-%m-%Y')

            data = {
                                    
                            "localizacion-mx":
                     { 
                     "Login":
                     { "rfc":rfc, "clave":clave
                     }, "Consulta":{ "Filtros":{ "fechadesde":fecha_actua, "rangoinicial":"", "rangofinal":"", "paginar":"" } }} } 
                         
            headers =  {'content-type': 'application/json','timeout':'500000'}
            Respuesta =  requests.post(str(url) + "/c_TipoOperacion", data=json.dumps(data), headers=headers)
            res =  json.loads(Respuesta.content.decode("utf-8"))                   
            
            for factor in res:  
                tipo_operacion = self.env['sat.tipooperacion'].search([('code', '=', factor['code'])])
                if tipo_operacion:
                    tipo_operacion.write(factor)
                else:
                    tipo_operacion.create(factor)
                _logger.info('\n******Fichero Cargado********\n')
            registro.actualizacion = fields.date.today()

        if self.sat_traslado == True:
            registro = self.env['actua.registro'].search([('modelo_id', '=', 'Motivo Traslado')])
            fecha_actu = datetime.datetime.strptime(str(registro.actualizacion), '%Y-%m-%d')
            fecha_actua = fecha_actu.strftime('%d-%m-%Y')

            data = {
                                    
                            "localizacion-mx":
                     { 
                     "Login":
                     { "rfc":rfc, "clave":clave
                     }, "Consulta":{ "Filtros":{ "fechadesde":fecha_actua, "rangoinicial":"", "rangofinal":"", "paginar":"" } }} } 
                                          
                   
            headers =  {'content-type': 'application/json','timeout':'500000'}
            Respuesta =  requests.post(str(url) + "/c_MotivoTraslado", data=json.dumps(data), headers=headers)
            res =  json.loads(Respuesta.content.decode("utf-8"))                   
            
            for trasl in res:  
                traslado = self.env['sat.traslado'].search([('code', '=', trasl['code'])])
                if traslado:
                    traslado.write(trasl)
                else:
                    traslado.create(trasl)
                _logger.info('\n******Fichero Cargado********\n')
            registro.actualizacion = fields.date.today()

        if self.sat_codigo_agrupador == True:
            registro = self.env['actua.registro'].search([('modelo_id', '=', 'Codigos Agrupadores')])
            fecha_actu = datetime.datetime.strptime(str(registro.actualizacion), '%Y-%m-%d')
            fecha_actua = fecha_actu.strftime('%d-%m-%Y')

            data = {
                                      
                            "localizacion-mx":
                     { 
                     "Login":
                     { "rfc":rfc, "clave":clave
                     }, "Consulta":{ "Filtros":{ "fechadesde":fecha_actua, "rangoinicial":"", "rangofinal":"", "paginar":"" } }} } 
                                           
            _logger.error('Datos enviados: %s', data)       
            headers =  {'content-type': 'application/json','timeout':'500000'}
            Respuesta =  requests.post(str(url) + "/c_CodigosAgrupadores", data=json.dumps(data), headers=headers)
            res =  json.loads(Respuesta.content.decode("utf-8"))                   
            _logger.error('data: %s ', res)
            
            ad = dict()
            for codigo in res: 
                _logger.info('\n******Cargando Fichero Codigo Agrupador Sat********\n') 
                codigo_agrupador = self.env['sat.account.code'].search([('key', '=', codigo['Key'])])
                if codigo_agrupador:
                    ad["key"] = codigo["Key"]
                    ad["name"] = codigo["Name"]
                    codigo_agrupador.write(ad)
                else:
                    ad["key"] = codigo["Key"]
                    ad["name"] = codigo["Name"] 
                    codigo_agrupador.create(ad)
                _logger.info('\n******Fichero Cargado********\n')   
            registro.actualizacion = fields.date.today()

        if self.sat_tasaocuota == True:
            registro = self.env['actua.registro'].search([('modelo_id', '=', 'Tasa o Cuota')])
            fecha_actu = datetime.datetime.strptime(str(registro.actualizacion), '%Y-%m-%d')
            fecha_actua = fecha_actu.strftime('%d-%m-%Y')

            data = {
                                                       
                      
                     "localizacion-mx":
                     { 
                     "Login":
                     { "rfc":rfc, "clave":clave
                     }, "Consulta":{ "Filtros":{ "fechadesde":fecha_actua, "rangoinicial":"", "rangofinal":"", "paginar":"" } }} } 
                                            
                   

            headers =  {'content-type': 'application/json','timeout':'500000'}
            Respuesta =  requests.post(str(url) + "/c_TasaOCuota", data=json.dumps(data), headers=headers)
            res =  json.loads(Respuesta.content.decode("utf-8"))                  
            _logger.error('data: %s ', res)
            ad = dict()
            for tasa in res: 
                tasa_cuota = self.env['sat.tasa.cuota'].search([('name', '=', tasa['RangoOFijo'])])
                if tasa_cuota:

                    ad['name'] = tasa['RangoOFijo']
                    ad['value_min'] = tasa['ValorMinimo']
                    ad['value_max'] = tasa['ValorMaximo']
                    ad['taxes'] = tasa['Impuesto']
                    ad['factor'] = tasa['Factor']
                    ad['retencion'] = tasa['Retencion']
                    ad['traslado'] = tasa['Traslado']
                    tasa_cuota.write(ad)
                else:
                    ad['name'] = tasa['RangoOFijo']
                    ad['value_min'] = tasa['ValorMinimo']
                    ad['value_max'] = tasa['ValorMaximo']
                    ad['taxes'] = tasa['Impuesto']
                    ad['factor'] = tasa['Factor']
                    ad['retencion'] = tasa['Retencion']
                    ad['traslado'] = tasa['Traslado']
                #ad['fecha_start'] = tasa['FechaInicioVigencia']                             
                    tasa_cuota.create(ad)
                _logger.info('\n******Fichero Cargado********\n')
            registro.actualizacion = fields.date.today()

        if self.sat_clavepedemiento == True:
            registro = self.env['actua.registro'].search([('modelo_id', '=', 'Claves Pedimentos')])
            fecha_actu = datetime.datetime.strptime(str(registro.actualizacion), '%Y-%m-%d')
            fecha_actua = fecha_actu.strftime('%d-%m-%Y')

            data = {
                                                       
                      
                     "localizacion-mx":
                     { 
                     "Login":
                     { "rfc":rfc, "clave":clave
                     }, "Consulta":{ "Filtros":{ "fechadesde":fecha_actua, "rangoinicial":"", "rangofinal":"", "paginar":"" } }} } 
                                            
                   

            headers =  {'content-type': 'application/json','timeout':'500000'}
            Respuesta =  requests.post(str(url) + "/c_ClavePedimento", data=json.dumps(data), headers=headers)
            res =  json.loads(Respuesta.content.decode("utf-8"))                  
            _logger.error('data: %s ', res)
            for clave in res: 
                pedimento = self.env['sat.clavepedimento'].search([('code', '=', clave['code'])])
                if pedimento:
                    pedimento.write(clave)  
                else:
                    pedimento.create(clave)
                _logger.info('\n******Fichero Cargado********\n')
            registro.actualizacion = fields.date.today()

        if self.pacs == True:
            registro = self.env['actua.registro'].search([('modelo_id', '=', 'PACS')])
            fecha_actu = datetime.datetime.strptime(str(registro.actualizacion), '%Y-%m-%d')
            fecha_actua = fecha_actu.strftime('%d-%m-%Y')

            data = {
                                                       
                      
                     "localizacion-mx":
                     { 
                     "Login":
                     { "rfc":rfc, "clave":clave
                     }, "Consulta":{ "Filtros":{ "fechadesde":fecha_actua, "rangoinicial":"", "rangofinal":"", "paginar":"" } }} } 
                                            
                   

            headers =  {'content-type': 'application/json','timeout':'500000'}
            Respuesta =  requests.post(str(url) + "/CTE_PAC", data=json.dumps(data), headers=headers)
            res =  json.loads(Respuesta.content.decode("utf-8"))                  
            _logger.error('data: %s ', res)
            ad = dict()
            for pac in res: 
                pacs = self.env['pac.timbres'].search([('name', '=', pac['PacID'])])
                if pacs:
                    ad['name'] = pac['PacID']
                    ad['nombre_pac'] = pac['NombrePac']
                    pacs.write(ad)
                else:
                    ad['name'] = pac['PacID']
                    ad['nombre_pac'] = pac['NombrePac']                                                        
                    pacs.create(ad)
            registro.actualizacion = fields.date.today()
        if self.sat_exportacion == True:
            registro = self.env['actua.registro'].search([('modelo_id', '=', 'Exportación')])
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
            Respuesta =  requests.post(str(url) + "/c_Exportacion", data=json.dumps(data), headers=headers)                
            res =  json.loads(Respuesta.content.decode("utf-8"))
            _logger.error('Respuestas: %s', res)
            for exportacion in res: 
                
                tipocarga = self.env['sat.exportacion'].search([('c_Exportacion', '=', exportacion['c_Exportacion'])])

                if tipocarga:
                    tipocarga.write(exportacion)  

                else:
                    tipocarga.create(exportacion)                           
                
                _logger.info('\n******Fichero Actualizado********\n')
            registro.actualizacion = fields.date.today()
        if self.sat_meses == True:
            registro = self.env['actua.registro'].search([('modelo_id', '=', 'Meses')])
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
            Respuesta =  requests.post(str(url) + "/c_meses", data=json.dumps(data), headers=headers)                
            res =  json.loads(Respuesta.content.decode("utf-8"))
            _logger.error('Respuestas: %s', res)
            for meses in res: 
                
                mes = self.env['sat.meses'].search([('c_Meses', '=', meses['c_Meses'])])

                if mes:
                    mes.write(meses)  

                else:
                    mes.create(meses)                           
                
                _logger.info('\n******Fichero Actualizado********\n')
            registro.actualizacion = fields.date.today()

        if self.sat_periodicidad == True:
            registro = self.env['actua.registro'].search([('modelo_id', '=', 'Periodicidad')])
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
            Respuesta =  requests.post(str(url) + "/c_periodicidad", data=json.dumps(data), headers=headers)                
            res =  json.loads(Respuesta.content.decode("utf-8"))
            _logger.error('Respuestas: %s', res)
            for periodicidad in res: 
                
                per = self.env['sat.periodicidad'].search([('c_Periodicidad', '=', periodicidad['c_Periodicidad'])])

                if per:
                    per.write(periodicidad)  

                else:
                    per.create(periodicidad)                           
                
                _logger.info('\n******Fichero Actualizado********\n')
            registro.actualizacion = fields.date.today()

        if self.sat_objetoimp == True:
            registro = self.env['actua.registro'].search([('modelo_id', '=', 'ObjetoImp')])
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
            Respuesta =  requests.post(str(url) + "/c_Objetoimp", data=json.dumps(data), headers=headers)                
            res =  json.loads(Respuesta.content.decode("utf-8"))
            _logger.error('Respuestas: %s', res)
            for impuesto in res: 
                
                obj = self.env['sat.objetoimp'].search([('c_ObjetoImp', '=', impuesto['c_ObjetoImp'])])

                if obj:
                    obj.write(impuesto)  

                else:
                    obj.create(impuesto)                           
                
                _logger.info('\n******Fichero Actualizado********\n')
            registro.actualizacion = fields.date.today()

    @api.onchange('sat_cfdi', 'sat_ce')
    def select_catalogos_cfdi33(self):
        if self.sat_cfdi == True:
            self.sat_colonia = True                        
            self.sat_codigo_postal = True            
            self.sat_localidad = True
            self.sat_estados = True
            self.sat_aduana = True
            self.sat_paises = True
            self.sat_municipio = True
            self.sat_producto = True            
            self.sat_udm = True
            self.sat_uso_cfdi = True
            self.sat_pedimento = True
            self.sat_arancel = True            
            self.sat_regimen_fiscal = True
            self.sat_impuestos = True
            self.sat_formas_pago = True
            self.sat_metodo_pago = True
            self.sat_tipos_relacion = True
            self.sat_patentes_aduanales = True
            self.sat_moneda = True
            self.sat_tipo_comprobante = True
            self.sat_tasaocuota = True
            self.sat_tipofactor = True
            self.sat_clavepedemiento = True
            self.sat_tipooperacion = True
            self.sat_traslado = True

        else:
            self.sat_colonia = False                        
            self.sat_codigo_postal = False                       
            self.sat_localidad = False
            self.sat_estados = False
            self.sat_aduana = False
            self.sat_paises = False
            self.sat_municipio = False
            self.sat_producto = False            
            self.sat_udm = False
            self.sat_uso_cfdi = False
            self.sat_pedimento = False
            self.sat_arancel = False            
            self.sat_regimen_fiscal = False
            self.sat_impuestos = False
            self.sat_formas_pago = False
            self.sat_metodo_pago = False
            self.sat_tipos_relacion = False
            self.sat_patentes_aduanales = False
            self.sat_moneda = False
            self.sat_tipo_comprobante = False
            self.sat_tasaocuota = False
            self.sat_tipofactor = False
            self.sat_clavepedemiento = False
            self.sat_tipooperacion = False
            self.sat_traslado = False

        if self.sat_ce == True:
            self.tipo_poliza = True
            self.sat_codigo_agrupador = True
            self.sat_bancos = True
            self.sat_metodopago = True
        else:
            self.tipo_poliza = False
            self.sat_codigo_agrupador = False
            self.sat_bancos = False
            self.sat_metodopago = False
    @api.model
    def update_countrys_sat(self):
        cr = self.env.cr
        instance_class_data = update_mx_data.ReturnCountryMxData()
        list_codes =instance_class_data.return_country_list()
        for code in list_codes:
            cr.execute("""
                update res_country set
                    sat_code = (select id
                    from res_country_sat_code where code=%s limit 1) where code=%s;
                """,(code[1],code[0]))
    
    @api.model
    def update_countrys_states_sat(self):
        cr = self.env.cr
        instance_class_data = update_mx_data.ReturnCountryMxData()
        list_codes =instance_class_data.return_states_list()
        for code in list_codes:
            cr.execute("""
                update res_country_state set
                    sat_code = (select id
                    from res_country_state_sat_code where code=%s limit 1) where code=%s and country_id = (select id from res_country where res_country.code = 'MX');
                """,(code[1],code[1]))
    
    
        


   
