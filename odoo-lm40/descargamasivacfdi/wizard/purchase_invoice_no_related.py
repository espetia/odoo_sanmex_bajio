# -*- encoding: utf-8 -*-

from odoo import api, fields, models, _, exceptions
import xmltodict
import base64
from xml.dom.minidom import parse, parseString
from odoo.exceptions import UserError, ValidationError
from lxml import etree as et
from odoo.addons.descargamasivacfdi.lib.cfdiclient import Validacion
import requests
import json
import urllib
import logging
_logger = logging.getLogger(__name__)


class cfdi_no_related(models.TransientModel):
    _name = 'cfdi.no.realted'  
     
    

    def get_default_relacion_registros(self):
        _logger.error('contexto: %s', self._context)
        invoice = self.env['account.move'].browse(self._context['active_id'])
        facturas = self.env['registro.descargas']
        facturas_reg = facturas.search([('rfc_emisor', '=', invoice.partner_id.rfc),('registro','=',False)])                     
        _logger.error('facturas_reg: %s', facturas_reg)
        return  facturas_reg

    cfdi_registro_id = fields.Many2many('registro.descargas', 'cfdi_no_related', 'registros_cfdi_id',
                                    'registro_id', string='CFDI Descargados', copy=False, default=get_default_relacion_registros)
    
     

    def cfdi_no_related(self):
        for registros in self.cfdi_registro_id:
            invoice = self.env['account.move'].browse(self._context['active_id']) 
            if registros.select == True:
                invoice.uuid_factura = registros.uuid_xml
                registros.registro = True
                registros.invoice_id = invoice.id
            defaults = len(registros.search([('select','=',True)]))        
            if defaults and (defaults > 1):
                raise exceptions.ValidationError("No puede seleccionar más de una opción") 
  
class cfdi_no_related_h_expense(models.TransientModel):
    _name = 'cfdi.no.realted.expense'  
     
    

    
    def buscar_gastos_multiple(self):
        gastos = self.env['hr.expense.sheet'].search([('state', 'in', ('post','done'))])
        _logger.error('Gastos: %s', gastos)
        if not gastos:
            raise UserError(_("Error!\nNotas de Gastos no encontradas"))
        else:

            for registros in self.env['registro.descargas'].search([('id','in', self._context['active_ids'] )]):
                for gasto in gastos:
                    for gasto_line in gasto.expense_line_ids:
                        _logger.error('gasto_line: %s', gasto_line.uuid_fact)
                        if registros.uuid_xml == gasto_line.uuid_fact:                
                            registros.registro = True
                            registros.nota_gasto = gasto.name
                        if registros.registro ==True:
                            raise UserError(_("Error!\nLos registros ya han sido comparados y encontrados")) 
                
        return True

     

            
            
            
            

    