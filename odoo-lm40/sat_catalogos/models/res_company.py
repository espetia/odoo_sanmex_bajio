# -*- encoding: utf-8 -*-

from odoo import api, fields, models, _
import time
import odoo
from lxml import etree as et
import base64
import tempfile
import ssl
from OpenSSL import crypto
import logging
_logger = logging.getLogger(__name__)


class account_move_concept_template(models.Model):
    _name = 'account.move.concept.template'

    move_type = fields.Selection([
                        ('in_invoice', 'Factura de Proveedor'),
                        ('out_invoice', 'Factura de Cliente'),
                        ('out_refund', 'Nota de Crédito de Cliente'),
                        ('outbound', 'Pago a Proveedor'),
                        ('inbound', 'Cobro de Cliente'),
                        ('in_refund', 'Nota de Crédito de Proveedor'),
                        ('pick_out', 'Albaran de salida'),
                        ('pick_int', 'Albaran de entrada'),
                        ('inter_trans', 'Transferencias Internas'),
                        ('inven_ajust', 'Ajuste de Inventario')], 
                    required=True, string='Tipo de póliza', 
        help='Elija el tipo de póliza para la cual aplicar esta plantilla. Solo puede haber una plantilla por tipo.')
    concept = fields.Text(string='Concepto', help='Escriba la plantilla, considere que el límite máximo son 300 caracteres una vez aplicado el formato.', required=True)
    company_id = fields.Many2one('res.company', string='Compañía')
                
    _sql_constraints = [('unique_move_type', 'unique(move_type, company_id)', 'Solamente puede haber una plantilla por tipo de póliza en cada empresa.')]


class res_company(models.Model):
    _inherit = 'res.company'
    
    
    pac_user    = fields.Char(string="Usuario PAC")
    pac_password = fields.Char(string="Contraseña PAC")
    pac_testing = fields.Boolean(string="Testing")
    pac_equipo_id = fields.Char(string="Equipo ID", help="Este dato lo entrega el PAC")    
    pac_user_4_testing      = fields.Char(string="Usuario")
    pac_password_4_testing  = fields.Char(string="Contraseña")
    pac_equipo_id_4_testing = fields.Char(string="Equipo ID", help="Este dato lo entrega el PAC")
    address_invoice_parent_company_id = fields.Many2one("res.partner", string='Invoice Company Address Parent', 
                                                        help="In this field should \
        placed the address of the parent company , independently if \
        handled a scheme Multi-company o Multi-Address.",
                                        domain="[('type', 'in', ('invoice','default','contact'))]")
    razonsocial = fields.Char(string='Razón social', size=250)    
    license_key = fields.Char(string='Clave de licenciamiento', size=40)
    concept_template_ids = fields.One2many('account.move.concept.template', 'company_id', 'Plantillas de Conceptos')
    auto_mode_enabled = fields.Boolean(string='Modo automático (C.E.)', default=True,
                                       help='Marque esta casilla para proporcionar las características de automatización en la contabilidad electrónica; se requiere una nueva clave de licenciamiento para activación.')        
    clave_acceso = fields.Char('UUID de Base de datos')
    cat_pacs = fields.Many2one('pac.timbres', 'PAC')
    url_pruebas_pac = fields.Char('URL de Pruebas')
    url_productivo_pac = fields.Char('URL de Producción')
    url_cancelacion_pac_prue = fields.Char('URL Cancelación Pruebas')
    url_cancelacion_pac_prodc = fields.Char('URL Cancelación Productivo')
    config_webservice = fields.Char("Id de registro", default=0, readonly=True)
    serie_cfdi_invoice = fields.Char(string="Serie Factura", size=12, help="Indique la Serie a utilizar para el CFDI (Opcional)")
    serie_cfdi_refund  = fields.Char(string="Serie Nota de Crédito", size=12, help="Indique la Serie a utilizar para el CFDI (Opcional)")   
    
    certificate_file = fields.Binary(string='Certificado (*.cer)',
                    filters='*.cer,*.certificate,*.cert', 
                    help='Seleccione el archivo del Certificado de Sello Digital (CSD). Archivo con extensión .cer')
    certificate_key_file = fields.Binary(string='Llave del Certificado (*.key)',
                    filters='*.key', 
                    help='Seleccione el archivo de la Llave del Certificado de Sello Digital (CSD). Archivo con extensión .key')
    certificate_password = fields.Char(string='Contraseña Certificado', size=64, invisible=False) 
    certificate_file_pem = fields.Binary(string='Certificado (PEM)',
                    filters='*.pem,*.cer,*.certificate,*.cert', 
                    help='Este archivo es generado a partir del CSD (.cer)')
    certificate_key_file_pem = fields.Binary(string='Llave del Certificado (PEM)',
                    filters='*.pem,*.key', help='Este archivo es generado a partir del CSD (.key)')
    certificate_pfx_file = fields.Binary(string='Certificado (PFX)',
                    filters='*.pfx', help='Este archivo es generado a partir del CSD (.cer)')
    date_start  = fields.Date(string='Vigencia de', help='Fecha de inicio de vigencia del CSD')
    date_end    = fields.Date(string='Vigencia hasta',  help='Fecha de fin de vigencia del CSD')
    serial_number = fields.Char(string='Número de Serie', size=64, 
                                help='Number of serie of the certificate')  
    estimulo_sat = fields.Boolean('Registro LCO')

    @api.onchange('certificate_password')
    def _onchange_certificate_password(self):
        warning = {}
        certificate_lib = self.env['facturae.certificate.library']
        certificate_file_pem = False
        certificate_key_file_pem = False
        cer_der_b64str  = self.certificate_file and base64.encodestring(self.certificate_file) or False
        key_der_b64str  = self.certificate_key_file and base64.encodestring(self.certificate_key_file) or False
        password        = self.certificate_password or False        
        if cer_der_b64str and key_der_b64str and password:
            if True:
                cer_pem_b64 = ssl.DER_cert_to_PEM_cert(base64.decodestring(self.certificate_file)).encode('UTF-8')
                _logger.error('cert: %s', cer_pem_b64)
                key_pem_b64 = certificate_lib.convert_key_cer_to_pem(base64.decodestring(self.certificate_key_file),
                                                                    str.encode(self.certificate_password))
                _logger.error('key_pem_b64: %s', key_pem_b64)
                pfx_pem_b64 = certificate_lib.convert_cer_to_pfx(cer_pem_b64, key_pem_b64,
                                                                 self.certificate_password)
                cert = crypto.load_certificate(crypto.FILETYPE_PEM, cer_pem_b64)
                x = hex(cert.get_serial_number())
                self.serial_number = x[1::2].replace('x','')
                date_start = cert.get_notBefore().decode("utf-8") 
                date_end = cert.get_notAfter().decode("utf-8") 
                self.date_start = date_start[:4] + '-' + date_start[4:][:2] + '-' + date_start[6:][:2]
                self.date_end = date_end[:4] + '-' + date_end[4:][:2] + '-' + date_end[6:][:2]
                self.certificate_file_pem       = base64.b64encode(cer_pem_b64)
                self.certificate_key_file_pem   = base64.b64encode(key_pem_b64)
                self.certificate_pfx_file       = base64.b64encode(pfx_pem_b64)
            else:
                warning = {
                    'title': _('Advertencia!'),
                    'message': _('El archivo del Certificado, la Llave o la Contraseña son incorrectas o no están definidas.\nPor favor revise')
                }
                self.certificate_file_pem = False,
                self.certificate_key_file_pem = False,
                self.certificate_pfx_file = False,
                
        else:
                warning = {
                    'title': _('Advertencia!'),
                    'message': _('Falta algún dato, revise que tenga el Certificado, la Llave y la contraseña correspondiente')
                }
        return {'warning': warning}    

    rfc = fields.Char(string='R.F.C.', size=15, help="RFC de la empresa SIN el prefijo MX", compute='_compute_address', inverse='_inverse_rfc')                        
    num_external = fields.Char(string="No. External", compute='_compute_address', inverse='_inverse_l10n_mx_street3')
    num_internal = fields.Char(string="No. Internal", compute='_compute_address', inverse='_inverse_l10n_mx_street4')
    
    sat_municipio_id = fields.Many2one('res.country.township.sat.code', string='Municipio', compute='_compute_address', inverse='_inverse_township_sat_id')
    sat_localidad_id = fields.Many2one('res.country.locality.sat.code', string='Localidad', compute='_compute_address', inverse='_inverse_locality_sat_id')
    codigopostal_sat_id = fields.Many2one('res.country.zip.sat.code', string='CP Sat', compute='_compute_address', inverse='_inverse_zip_sat_id')
    colonia_sat_id = fields.Many2one('res.colonia.zip.sat.code', string='Colonia Sat', compute='_compute_address', inverse='_inverse_colonia_sat_id')

    def _compute_address(self):
        for company in self.filtered(lambda company: company.partner_id):
            address_data = company.partner_id.sudo().address_get(adr_pref=['contact'])
            if address_data['contact']:
                partner = company.partner_id.browse(address_data['contact'])
                company.street = partner.street  
                company.street2 = partner.street2   
                company.city = partner.city
                company.zip = partner.zip
                company.state_id = partner.state_id
                company.country_id = partner.country_id                   
                company.num_external = partner.num_external
                company.num_internal = partner.num_internal
                company.rfc = partner.rfc
                company.sat_municipio_id = partner.sat_municipio_id.id
                company.sat_localidad_id = partner.sat_localidad_id.id
                company.codigopostal_sat_id = partner.sat_codigopostal_id.id
                company.colonia_sat_id = partner.colonia_sat_id.id

    def _inverse_l10n_mx_street3(self):
        for company in self:
            company.partner_id.num_external = company.num_external
                
    def _inverse_l10n_mx_street4(self):
        for company in self:
            company.partner_id.num_internal = company.num_internal

    def _inverse_rfc(self):
        for company in self:
            company.partner_id.rfc = company.rfc               

    def _inverse_township_sat_id(self):
        for company in self:
            company.partner_id.sat_municipio_id = company.sat_municipio_id.id

    def _inverse_locality_sat_id(self):
        for company in self:
            company.partner_id.sat_localidad_id = company.sat_localidad_id.id
        
    def _inverse_zip_sat_id(self):
        for company in self:
            company.partner_id.sat_codigopostal_id = company.codigopostal_sat_id.id
        
    def _inverse_colonia_sat_id(self):
        for company in self:
            company.partner_id.colonia_sat_id = company.colonia_sat_id.id


    @api.onchange('cat_pacs', 'pac_testing')
    def url_timbre_cancelacion(self):
        if self.cat_pacs == 'SIFEI' and self.pac_testing == False:
            self. url_productivo_pac = 'https://sat.sifei.com.mx:8443/SIFEI/SIFEI?wsdl'
            self.url_cancelacion_pac_prodc = 'https://sat.sifei.com.mx:9000/CancelacionSIFEI/Cancelacion?wsdl'
            self.url_pruebas_pac = ''
            self.url_cancelacion_pac_prue = ''
        else:
            self.url_pruebas_pac = 'http://devcfdi.sifei.com.mx:8080/SIFEI33/SIFEI?wsdl'
            self.url_cancelacion_pac_prue = 'http://devcfdi.sifei.com.mx:8888/CancelacionSIFEI/Cancelacion?wsdl'
            self. url_productivo_pac = ''
            self.url_cancelacion_pac_prodc = ''

    @api.onchange('codigopostal_sat_id')
    def onchange_zip_sat_id_company(self):
        if self.codigopostal_sat_id:
            self.zip = self.codigopostal_sat_id.code   

            state_sat_code = self.codigopostal_sat_id.state_sat_code            
            state_id = self.env['res.country.state'].search([('sat_code','=',state_sat_code)])            
            if state_id:
                self.state_id = state_id[0].id                
                self.country_id = state_id[0].country_id.id                

            colonia_sat_id = self.env['res.colonia.zip.sat.code'].search([('zip_sat_code_char','=',self.codigopostal_sat_id.code)])
            
            if colonia_sat_id:
                self.colonia_sat_id = colonia_sat_id[0].id

    @api.onchange('state_id')
    def onchange_domain_sat_list_company(self):
        domain = {}
        if self.state_id:                       
            township_ids = self.env['res.country.township.sat.code'].search([('state_sat_code','=',self.state_id.sat_code.code)])
            self.sat_municipio_id = township_ids.filtered(lambda r: r.code == self.codigopostal_sat_id.township_sat_code).id
            
            if township_ids:
                domain.update(
                    {
                        'sat_municipio_id':[('id','in',[x.id for x in township_ids])]
                    })
             
            locality_ids = self.env['res.country.locality.sat.code'].search([('state_sat_code','=',self.state_id.sat_code.code)])
            self.sat_localidad_id = locality_ids.filtered(lambda r: r.code == self.codigopostal_sat_id.locality_sat_code).id
            if locality_ids:
                domain.update(
                    {
                        'sat_localidad_id':[('id','in',[x.id for x in locality_ids])]
                    })        

        return {'domain': domain}

    
    
    

    @api.onchange('rfc')
    def onchange_colonia_sat_id(self):
        if self.rfc:
            if self.rfc[0:2] == 'MX':
                self.vat = self.rfc
                #self.vat_split = self.rfc[2:]
            else:
                self.vat = 'MX'+self.rfc
                #self.vat_split = self.rfc

    
    @api.model
    def _assembly_concept(self, mv_type, invoice=None, voucher=None):
        self.ensure_one()
        if mv_type == 'in_invoice':
            move = 'Facturas de Proveedor'
        elif mv_type == 'out_invoice':
            move = 'Facturas de Cliente'
        elif mv_type == 'out_refund':
            move = u'Notas de Cr\xe9dito de cliente'
        elif mv_type == 'outbound':
            move = 'Pagos a Proveedor'
        elif mv_type == 'inbound':
            move = 'Cobros de Cliente'
        elif mv_type == 'out_refund':
            move = u'Notas de Cr\xe9dito de Proveedor'
        elif mv_type == 'pick_int':
            move = 'Albaran de entrada'
        
        elif mv_type == 'inter_trans':
            move = 'Transferencias Internas'
        elif mv_type == 'inven_ajust':
            move = 'Ajuste de Inventario'
        templates = [ ln.concept for ln in self.concept_template_ids if ln.move_type == mv_type ]
        if len(templates):
            concept_parts = templates[0].split('___')
            if len(concept_parts) != 2:
                raise UserError(_('Plantilla de concepto incorrecta.\n\nRevise que la plantilla para %s cuenta con argumentos.') % (move))
            try:
                return concept_parts[0] % eval(concept_parts[1])
            except Exception as e:
                logging.getLogger(self._name).exception('Error evaluating Template for Account Move Concept.')
                logging.getLogger(self._name).exception(e)
                raise UserError(_('Plantilla de concepto errónea\n\nRevise que la plantilla para %s cuenta con el formato requerido y que los campos especificados existen en el modelo.') % (move))
        return False


       
    


    
        