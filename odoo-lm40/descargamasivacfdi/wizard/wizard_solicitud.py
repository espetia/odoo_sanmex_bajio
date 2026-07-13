from odoo.addons.descargamasivacfdi.lib.cfdiclient import Autenticacion
from odoo.addons.descargamasivacfdi.lib.cfdiclient import Fiel
from odoo.addons.descargamasivacfdi.lib.cfdiclient import SolicitaDescarga
from odoo import api, fields, models, _
import base64
import datetime
from datetime import date
# odoo.addons.descargamasivacfdi.lib.cfdiclient
import logging
_logger = logging.getLogger(__name__)
from odoo.exceptions import UserError, RedirectWarning, ValidationError


class wizard_solicita_descarga(models.TransientModel):

    _name = 'solictud.descarga'

    rfc_solicita = fields.Char(related="company_id.rfc", string='RFC del solicitante', readonly=True)
    date_init = fields.Datetime('Fecha inicial')
    date_end = fields.Datetime('Fecha final')
    certificate_file = fields.Binary(related="company_id.certificate_file_FIEL", string='Certificado (*.cer)', filters='*.cer,*.certificate,*.cert', readonly=True)
    certificate_key_file = fields.Binary(related="company_id.certificate_key_file_FIEL", string='Llave del Certificado (*.key)', filters='*.key', readonly=True)
    certificate_password = fields.Char(string='Contraseña Certificado', size=64) 
    tipo_petición = fields.Selection([
                ('cfdi', 'CFDI'),
                ('meta', 'Metadata')                                
                ], string='Tipo petición')
    tipo_cfdi = fields.Selection([
                ('recibido', 'Recibidos'),
                ('emitido', 'Emitidos')                                
                ], string='Tipo')
    company_id = fields.Many2one('res.company', string='Compañia', default=lambda self: self.env['res.company']._company_default_get('solictud.descarga'))

    
    def solictar_descarga(self):
        FIEL_KEY = self.certificate_key_file
        FIEL_CER = self.certificate_file
        FIEL_PAS = self.certificate_password
        cer_der = base64.b64decode(self.certificate_file)
        key_der = base64.b64decode(self.certificate_key_file)
        fiel = Fiel(cer_der, key_der, FIEL_PAS)   
            
        auth = Autenticacion(fiel)  
        _logger.error('auth: %s', auth)      
        token = auth.obtener_token()
       
        #Solicitar descarga#
        descarga = SolicitaDescarga(fiel)             
        token = token  
        tipo_solicitud = dict(self._fields['tipo_petición'].selection).get(self.tipo_petición)  
        rfc_solicitante = self.rfc_solicita
        rfc_receptor = self.rfc_solicita        
        fecha_inicial = fields.Datetime.from_string(str(self.date_init)) 
        fecha_inicial = fecha_inicial.replace(hour=00)
        fecha_inicial = fecha_inicial.replace(minute=00)
        fecha_inicial = fecha_inicial.replace(second=00)     
        fecha_final = fields.Datetime.from_string(str(self.date_end))
        fecha_final = fecha_final.replace(hour=23)
        fecha_final = fecha_final.replace(minute=59)
        fecha_final = fecha_final.replace(second=59)
        ad = dict()
        if fecha_final < fecha_inicial:
            raise UserError(_("Error !!!\nLa fecha final es menor a la inicial, por favor revise."))
       
        if self.tipo_cfdi == 'recibido':
            result = descarga.solicitar_descarga(token, rfc_solicitante, fecha_inicial, fecha_final, rfc_receptor=rfc_receptor, tipo_solicitud=tipo_solicitud)
            _logger.error('resultado_recibidos: %s', result)
            ad['id_peticion'] = result['id_solicitud']
            ad['status'] = result['mensaje']
            ad['tipo_peticion'] = dict(self._fields['tipo_petición'].selection).get(self.tipo_petición)
            ad['tipo_factura'] =  dict(self._fields['tipo_cfdi'].selection).get(self.tipo_cfdi)
            ad['date_ini'] = self.date_init
            ad['date_end'] = self.date_end
            self.env['peticiones.cfdi'].create(ad)
        if self.tipo_cfdi == 'emitido':
            result = descarga.solicitar_descarga(token, rfc_solicitante, fecha_inicial, fecha_final, rfc_emisor=rfc_solicitante, tipo_solicitud=tipo_solicitud)
            _logger.error('resultado_emtidos: %s', result)
            ad['id_peticion'] = result['id_solicitud']
            ad['status'] = result['mensaje']
            ad['tipo_peticion'] = dict(self._fields['tipo_petición'].selection).get(self.tipo_petición)
            ad['tipo_factura'] =  dict(self._fields['tipo_cfdi'].selection).get(self.tipo_cfdi)
            ad['date_ini'] = self.date_init
            ad['date_end'] = self.date_end
            self.env['peticiones.cfdi'].create(ad)
        
        
        
        

