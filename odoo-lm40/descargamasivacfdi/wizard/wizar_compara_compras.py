# -*- coding: utf-8 -*-

from odoo import api, fields, models, _
from odoo.exceptions import UserError
import logging
_logger = logging.getLogger(__name__)

class comparacompras(models.TransientModel):
    _name = 'wizard.compara.compras'


    
    def buscar_factura_multiple(self):
        facturas_provee = self.env['account.move'].search([('type','=','in_invoice')])
        _logger.error('facturas: %s', facturas_provee)
        for registros in self.env['registro.descargas'].search([('id','in', self._context['active_ids'] )]):
            for factura in facturas_provee:
               
                if registros.uuid_xml == factura.uuid_factura:                
                    registros.registro = True
                    registros.invoice_id = factura.id
                """if registros.registro ==True:
                    raise UserError(_("Error!\nLos registros ya han sido comparados y encontrados"))"""   
                
        return True


    
