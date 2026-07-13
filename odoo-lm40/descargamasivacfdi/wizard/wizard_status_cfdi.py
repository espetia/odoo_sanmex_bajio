# -*- coding: utf-8 -*-

from odoo import api, fields, models, _
from odoo.exceptions import UserError
from odoo.addons.descargamasivacfdi.lib.cfdiclient import Validacion
import logging
_logger = logging.getLogger(__name__)

class wizardstatus(models.TransientModel):
    _name = 'wizard.status.cfdi'


    
    def estatus_cfdi(self):       
        
       
        for registros in self.env['registro.descargas'].search([('id','in', self._context['active_ids'] )]):
            add = dict()
            validacion = Validacion()
            rfc_emisor = registros.rfc_emisor
            rfc_receptor = registros.rfc_receptor
            if registros.tipo_docto == 'P':
                total = str(0)
            else:
                total = str(registros.amount_total)
            uuid = registros.uuid_xml
            estado = validacion.obtener_estado(rfc_emisor, rfc_receptor, total, uuid)
            _logger.error('estado: %s', estado)
            add['status_cfdi'] = estado['estado']
            add['es_cancelable'] = estado['es_cancelable']        
            add['codigo_status'] = estado['codigo_estatus']
            registros.write(add)
                
                
        return True
