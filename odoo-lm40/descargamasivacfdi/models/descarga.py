
from odoo import api, fields, models, _
from odoo.exceptions import UserError
import odoo.addons.decimal_precision as dp
import time
from werkzeug import url_encode
import logging
_logger = logging.getLogger(__name__)
import base64
from odoo.addons.descargamasivacfdi.lib.cfdiclient import Autenticacion
from odoo.addons.descargamasivacfdi.lib.cfdiclient import Fiel
from odoo.addons.descargamasivacfdi.lib.cfdiclient import SolicitaDescarga
from odoo.addons.descargamasivacfdi.lib.cfdiclient import VerificaSolicitudDescarga
from odoo.addons.descargamasivacfdi.lib.cfdiclient import DescargaMasiva
from odoo.addons.descargamasivacfdi.lib.cfdiclient import Validacion
import zipfile
from zipfile import ZipFile
import datetime
import os
import json
import io
import tempfile
import sys
from lxml import etree as et
from base64 import b64decode as b64dec, b64encode as b64enc
from xml.dom.minidom import parse, parseString


class peticionescfdi(models.Model):
    _name = "peticiones.cfdi"

    name = fields.Char("Folio Interno", default=lambda self: _('New'), readonly=True)
    descarga = fields.Boolean('Descargada', readonly=True)
    id_peticion = fields.Char('Id de Petición', readonly=True)
    tipo_peticion = fields.Char('Tipo Petición', readonly=True)
    status = fields.Char('Estado de Petición', readonly=True)
    date_ini = fields.Datetime('Fecha inicial', readonly=True)
    date_end = fields.Datetime('Fecha final', readonly=True)
    usuario_id = fields.Many2one('res.users', string='Usuario', readonly=True, default=lambda self: self.env.user)
    tipo_factura = fields.Char('Tipo', readonly=True)
    estado_solicitud = fields.Selection([
                ('1', 'Aceptada'),
                ('2', 'En Proceso'),
                ('3', 'Terminada'),
                ('4', 'Error'),
                ('5', 'Rechadaza'),
                ('6', 'Vencida')                              
                ], string='Estado solicitud', readonly=True)
    numero_cfdis = fields.Integer('Numero de CFDIS', readonly=True)  
    id_paquete = fields.Char('Id Paquete')
    codigo_descarga = fields.Char('Codigo de descarga') 
    paquetes_ids = fields.One2many('peticiones.cfdi.line', 'peticiones_id', string="Paquetes", readonly=True)

    @api.model
    def create(self, vals):
        
        vals['name'] = self.env['ir.sequence'].next_by_code('peticionescfdi') or _('New')

        result_1 = super(peticionescfdi, self).create(vals)
        return result_1


class peticionescfdilines(models.Model):
    _name = "peticiones.cfdi.line"

    peticiones_id = fields.Many2one('peticiones.cfdi', string="Peticiones")
    id_paquete = fields.Char('Id Paquete')
    codigo_descarga = fields.Char('Codigo de descarga')
    filename = fields.Char(string='Archivo', size=128)
    attachment_id = fields.Binary('Archivo Descargado')
    unzip_file = fields.Boolean('Desempaquetado')

    def _find_file_in_addons(self, directory, filename):
       
        addons_paths = tools.config['addons_path'].split(',')
        actual_module = directory.split('/')[0]
        if len(addons_paths) == 1:
            return os.path.join(addons_paths[0], directory, filename)
        for pth in addons_paths:
            for subdir in os.listdir(pth):
                if subdir == actual_module:
                    return os.path.join(pth, directory, filename)

        return False

    def do_something_with_xml_attachment(self, attach):

        return True

    def descomprimir(self):
        
        add = dict()
        ruta_zip = self.attachment_id
        filename = self.filename
        ruta_extraccion = "/tmp/"
        rutaarchivo = "/tmp/"
        password = None
         # #################desempaquetado de archivo petición CFDI#############################
        fstamped = io.BytesIO(base64.b64decode(ruta_zip))
        with zipfile.ZipFile(fstamped, "r") as zf:            
            zf.extractall(pwd=password, path=ruta_extraccion)  
            _logger.error('zf1: %s', zf)         
            for xml in zf.namelist():
                _logger.error('xml: %s', xml)

                if xml.endswith('.zip'):
                    with ZipFile(ruta_extraccion + xml, 'r') as zipObj:
                        zipObj.extractall(pwd=password, path=ruta_extraccion)
                        _logger.error('xml_1: %s', xml)
                for xml_1 in zipObj.namelist():
                    if xml_1.endswith('.xml'):   
                                   
                        contenido = open(ruta_extraccion+ xml_1, 'rb').read()
                        xml_file = open(rutaarchivo+ xml_1, 'wb').write(contenido)                
                        xml_file = open(rutaarchivo+ xml_1, 'rb').read()
                        decodificado = base64.b64encode(xml_file) 
                        decodificado = base64.decodestring(decodificado)
                        decodificado_1 = decodificado.decode("utf-8").replace('\r\n','')                  
                        lines = contenido.decode('utf8').strip()
                        try:
                            parser = et.XMLParser(no_network=True)
                            xml_doc = et.ElementTree(et.fromstring(decodificado_1, parser))
                            xml_comprobante = xml_doc.getroot()                    
                            if xml_comprobante.attrib['Version'] == '4.0':                    
                                xml_comp = xml_comprobante.find('{http://www.sat.gob.mx/cfd/4}Comprobante')
                            else:
                                xml_comp = xml_comprobante.find('{http://www.sat.gob.mx/cfd/3}Comprobante')  
                        except:
                            result = lines
                            archivo = open(rutaarchivo+"xmlmalo.txt", "w")
                            archivo.write(lines)
                            archivo.close()
                            _logger.error('result: %s', result)

                        serie = xml_comprobante.attrib                        
                        folio = ""
                        series = ""                       
                        for atributo in serie:
                            if atributo == 'Serie':
                                series = serie['Serie'] 
                            if atributo =='Folio':
                                folio = serie['Folio'].replace('"','')   
                        
                        # folio_fact = xml_comprobante.attrib['Folio'].replace('"','')                        
                        if xml_comprobante.attrib['Version'] == '4.0':
                            Emisor = xml_comprobante.find('{http://www.sat.gob.mx/cfd/4}Emisor')
                            Receptor = xml_comprobante.find('{http://www.sat.gob.mx/cfd/4}Receptor')
                            comp_timbre = xml_comprobante.find('{http://www.sat.gob.mx/cfd/4}Complemento')
                        else:

                            Emisor = xml_comprobante.find('{http://www.sat.gob.mx/cfd/3}Emisor')
                            Receptor = xml_comprobante.find('{http://www.sat.gob.mx/cfd/3}Receptor')
                            comp_timbre = xml_comprobante.find('{http://www.sat.gob.mx/cfd/3}Complemento')
                        Emisor_rfc = Emisor.attrib['Rfc']                       
                        Receptor_rfc = Receptor.attrib['Rfc']
                        tipo_comprobante = xml_comprobante.attrib['TipoDeComprobante']
                        total = xml_comprobante.attrib['Total']                        
                        timbre_fiscal = comp_timbre.find('{http://www.sat.gob.mx/TimbreFiscalDigital}TimbreFiscalDigital')            
                        
                        if tipo_comprobante == 'P':
                            if xml_comprobante.attrib['Version'] == '4.0':
                                Node_pago = comp_timbre.find('{http://www.sat.gob.mx/Pagos20}Pagos')                    
                                Node_pago_1 = Node_pago.find('{http://www.sat.gob.mx/Pagos20}Pago')
                            else:

                                Node_pago = comp_timbre.find('{http://www.sat.gob.mx/Pagos}Pagos')                    
                                Node_pago_1 = Node_pago.find('{http://www.sat.gob.mx/Pagos}Pago')                    
                            total = Node_pago_1.attrib['Monto']                    
                        UUID = timbre_fiscal.attrib['UUID'].upper()
                        fecha_timbre = timbre_fiscal.attrib['FechaTimbrado'].replace('T',' ')


                        filename = UUID + '.xml'                      
                        # #################creación de registro#############################                          
                        add['file_xml'] = base64.encodestring(str.encode(decodificado_1))
                        add['filename'] = filename
                        add['folio_factura'] = folio
                        add['serie_factura'] = series
                        add['uuid_xml'] = UUID
                        add['rfc_emisor'] = Emisor_rfc
                        add['rfc_receptor'] = Receptor_rfc
                        add['tipo_docto'] = tipo_comprobante
                        add['tipo_peticion'] = self.peticiones_id.tipo_peticion
                        add['fecha_cfdi'] = fecha_timbre
                        add['amount_total'] = total
                        add['id_peticion'] = self.peticiones_id.id
                        self.env['registro.descargas'].create(add)
                        self.unzip_file = True
                        
                    # #################desempaquetado de archivo petición Metadata#############################
                    if xml_1.endswith('.txt'):
                        
                        contenido = open(ruta_extraccion + xml_1, 'r')
                        i = 1                               
                        for meta_data in contenido.readlines():
                            
                            if i > 1:
                                CadenaSeparadaPor = meta_data.split('~')                                      
                           
                                add['uuid_xml'] = CadenaSeparadaPor[0]
                                add['rfc_emisor'] = CadenaSeparadaPor[1]
                                add['rfc_receptor'] = CadenaSeparadaPor[3]
                                add['tipo_docto'] = CadenaSeparadaPor[9]
                                add['tipo_peticion'] = self.peticiones_id.tipo_peticion
                                add['fecha_cfdi'] = CadenaSeparadaPor[6]
                                add['amount_total'] = CadenaSeparadaPor[8]
                                add['id_peticion'] = self.peticiones_id.id
                                self.env['registro.descargas'].create(add) 

                            i += 1
                        self.unzip_file = True


class registro_descarga(models.Model):
    _name = "registro.descargas"

    name = fields.Char("Folio Interno", default=lambda self: _('New'), readonly=True)
    file_xml = fields.Binary('XML')
    filename = fields.Char('Nombre archivo')
    uuid_xml = fields.Char('UUID Factura', readonly=True)
    rfc_emisor = fields.Char('RFC Emisor', readonly=True)
    rfc_receptor = fields.Char('RFC Receptor', readonly=True)
    tipo_docto = fields.Char('Tipo de Documento', readonly=True)
    tipo_peticion = fields.Char('Tipo de solicitud', readonly=True)
    amount_total = fields.Monetary('Total Factura', readonly=True)
    currency_id = fields.Many2one('res.currency', string="Moneda", required=False, readonly=True,
        default=lambda self: self.env.user.company_id.currency_id.id)
    fecha_cfdi = fields.Datetime('Fecha de Timbrado', readonly=True)
    registro = fields.Boolean('Relacionada', readonly=True)    
    id_peticion = fields.Many2one('peticiones.cfdi', string='ID Petición', readonly=True)
    usuario_id = fields.Many2one('res.users', string='Usuario', readonly=True, default=lambda self: self.env.user)
    status_cfdi = fields.Char('Estatus CFDI', readonly=True)
    es_cancelable = fields.Char('Es cancelable', readonly=True)    
    codigo_status = fields.Char('Código Estatus', readonly=True)
    invoice_id = fields.Many2one('account.move', string='Factura relacionada', readonly=True)
    select = fields.Boolean('Seleccionar')
    folio_factura = fields.Char('Folio Factura', readonly=True)
    serie_factura = fields.Char('Serie Factura', readonly=True)

    @api.model
    def create(self, vals):
        
        vals['name'] = self.env['ir.sequence'].next_by_code('registro_descarga') or _('New')

        result = super(registro_descarga, self).create(vals)
        return result
    
    # @api.multi
    def buscar_factura(self):
        facturas_provee = self.env['account.move'].search([('type','=','in_invoice')])
        _logger.error('facturas: %s', facturas_provee)
        for factura in facturas_provee:
           
            if self.uuid_xml == factura.uuid_factura:                
                self.registro = True
                self.invoice_id = factura.id

        return True

    def consulta_estatus(self):
        add = dict()
        validacion = Validacion()
        rfc_emisor = self.rfc_emisor
        rfc_receptor = self.rfc_receptor
        if self.tipo_docto == 'P':
            total = str(0)
        else:
            total = str(self.amount_total)
        uuid = self.uuid_xml
        estado = validacion.obtener_estado(rfc_emisor, rfc_receptor, total, uuid)
        _logger.error('estado: %s', estado)
        add['status_cfdi'] = estado['estado']
        add['es_cancelable'] = estado['es_cancelable']        
        add['codigo_status'] = estado['codigo_estatus']
        self.write(add)


class wizard_verificar_solicitud(models.TransientModel):

    _name = 'verificar.solicitud'

    certificate_file = fields.Binary(related="company_id.certificate_file_FIEL", string='Certificado (*.cer)', filters='*.cer,*.certificate,*.cert', readonly=True)
    certificate_key_file = fields.Binary(related="company_id.certificate_key_file_FIEL", string='Llave del Certificado (*.key)', filters='*.key', readonly=True)
    certificate_password = fields.Char(string='Contraseña Certificado', size=64) 
    rfc_solicita = fields.Char(related="company_id.rfc", string='RFC del solicitante', readonly=True)
    company_id = fields.Many2one('res.company', string='Compañia', default=lambda self: self.env['res.company']._company_default_get('verificar.solicitud'))

    def _get_default_id(self):
        peticion = self.env['peticiones.cfdi'].search([('id','in', self._context['active_ids'] )])    
             
        return peticion and peticion.id or False
    solicitud_id = fields.Many2one('peticiones.cfdi', string='solicitud', default=_get_default_id)
    id_peticion = fields.Char(related='solicitud_id.id_peticion', string="Id Petición", readonly=True)

    def consulta_solicitud(self):
        
        FIEL_KEY = self.certificate_key_file
        FIEL_CER = self.certificate_file
        FIEL_PAS = self.certificate_password
        cer_der = base64.b64decode(self.certificate_file)
        key_der = base64.b64decode(self.certificate_key_file)
        fiel = Fiel(cer_der, key_der, FIEL_PAS)        
        auth = Autenticacion(fiel)
        token = auth.obtener_token()        
        v_descarga = VerificaSolicitudDescarga(fiel)       
        rfc_solicitante = self.rfc_solicita        
        id_solicitud = self.id_peticion

        result = v_descarga.verificar_descarga(token, rfc_solicitante, id_solicitud)
        _logger.error('result: %s', result)

        if result['cod_estatus'] != '5000': 
            raise UserError(_("Error:\n\n %s" % str(result['cod_estatus'])+ ' '+ result['mensaje'] ))

        add = dict()
        add_line = dict()
        add['estado_solicitud'] = result['estado_solicitud']
        add['numero_cfdis'] = result['numero_cfdis']
        self.solicitud_id.write(add)
        for paquete in result['paquetes']:
            add_line['id_paquete'] = paquete
            add_line['peticiones_id'] = self.solicitud_id.id
            self.env['peticiones.cfdi.line'].create(add_line)


class wizard_descarga_cfdi(models.TransientModel):
    _name = 'descarga.cfdi'

    certificate_file = fields.Binary(related="company_id.certificate_file_FIEL", string='Certificado (*.cer)', filters='*.cer,*.certificate,*.cert', readonly=True)
    certificate_key_file = fields.Binary(related="company_id.certificate_key_file_FIEL", string='Llave del Certificado (*.key)', filters='*.key', readonly=True)
    certificate_password = fields.Char(string='Contraseña Certificado', size=64) 
    rfc_solicita = fields.Char(related="company_id.rfc", string='RFC del solicitante', readonly=True)
    company_id = fields.Many2one('res.company', string='Compañia', default=lambda self: self.env['res.company']._company_default_get('verificar.solicitud'))
    
    def _get_default_id_descarga(self):
        id_paquete = self.env['peticiones.cfdi.line'].search([('id','in', self._context['active_ids'] )])
        peticion = self.env['peticiones.cfdi'].search([('id','=',id_paquete.peticiones_id.id )])            
        return peticion and peticion.id or False

    solicitud_id = fields.Many2one('peticiones.cfdi', string='solicitud', default=_get_default_id_descarga)
    id_paquete = fields.Char(related='solicitud_id.paquetes_ids.id_paquete', string="Id Paquete", readonly=True)

    def _find_file_in_addons(self, directory, filename):
        
        addons_paths = tools.config['addons_path'].split(',')
        actual_module = directory.split('/')[0]
        if len(addons_paths) == 1:
            return os.path.join(addons_paths[0], directory, filename)
        for pth in addons_paths:
            for subdir in os.listdir(pth):
                if subdir == actual_module:
                    return os.path.join(pth, directory, filename)

        return False

    def descargacfdi(self):
        FIEL_KEY = self.certificate_key_file
        FIEL_CER = self.certificate_file
        FIEL_PAS = self.certificate_password
        cer_der = base64.b64decode(self.certificate_file)
        key_der = base64.b64decode(self.certificate_key_file)
        fiel = Fiel(cer_der, key_der, FIEL_PAS)        
        auth = Autenticacion(fiel)
        token = auth.obtener_token()
        descarga = DescargaMasiva(fiel)
        rfc_solicitante = self.rfc_solicita
        id_paquete = self.id_paquete
        result = descarga.descargar_paquete(token, rfc_solicitante, id_paquete)
        _logger.error('result: %s', result) 
        add = dict()       
        if result['cod_estatus'] != '5000': 
            raise UserError(_("Error:\n\n %s" % str(result['cod_estatus'])+ ' '+ result['mensaje'] ))

        # add = dict()  
        paquete_b64 = result['paquete_b64']
        add['codigo_descarga'] = str(result['cod_estatus'])+ ' '+ str(result['mensaje']) 
        self.solicitud_id.descarga = True
        fname = self.id_paquete + '.zip'
        (descriptor, zipname,) = tempfile.mkstemp('eaccount_', '__asti_')
        zipDoc = ZipFile(zipname, 'w')
        xmlContent = b64dec(paquete_b64)
        zipDoc.writestr(fname, xmlContent)
        zipDoc.close()
        os.close(descriptor)             
        add['attachment_id'] = b64enc(open(zipname, 'rb').read())
        add['filename'] = fname
        id_paquete = self.env['peticiones.cfdi.line'].search([('id','in', self._context['active_ids'] )])
        id_paquete.write(add)
