# -*- encoding: utf-8 -*-

from odoo import api, fields, models, _
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


class invoice_purchase(models.Model):
    _inherit = 'account.move'

    def action_cancel(self):
        res = super(invoice_purchase, self).action_cancel()
        cfdi_descarga = self.env['registro.descargas'].search([('invoice_id','=',self.id)])        
        for inv in cfdi_descarga:
            inv.registro = False
            inv.invoice_id = ""      

        return res

    def invoice_validate(self):
        res = super(invoice_purchase, self).invoice_validate()

        for rec in self:
            if rec.type in ('in_invoice', 'in_refund'):
                if rec.valida_nosat == False:
                    
                    adjunto_xml_id = self.env['ir.attachment'].search([('res_model', '=', 'account.invoice'), ('res_id', '=', rec.id), ('name', 'ilike', '.xml')], limit=1)
                    if not adjunto_xml_id:
                        raise UserError(_('No Puede Validar la Factura o Nota de Credito sin el archivo XML...'))
                    elif adjunto_xml_id:
                        uuid = False
                        
                        for att in adjunto_xml_id:
                            xml_data = base64.b64decode(att.datas).replace(b'http://www.sat.gob.mx/cfd/3 ', b'').replace(b'TipoDeComprobante=',b'tipodocumento=').replace(b'Rfc=',b'rfc=').replace(b'Fecha=',b'fecha=').replace(b'Total=',b'total=').replace(b'Folio=',b'folio=').replace(b'Serie=',b'serie=')
                            res = False
                            
                            xmlTree = et.ElementTree(et.fromstring(xml_data))
                            vouchNode = xmlTree.getroot()
                            uuid = vouchNode.find('{http://www.sat.gob.mx/cfd/3}Complemento').find('{http://www.sat.gob.mx/TimbreFiscalDigital}TimbreFiscalDigital').attrib['UUID'].upper()
                            rfc_emisor = vouchNode.find('{http://www.sat.gob.mx/cfd/3}Emisor').attrib['rfc'].upper()
                            rfc_receptor = vouchNode.find('{http://www.sat.gob.mx/cfd/3}Receptor').attrib['rfc'].upper()
                            monto_total = float(vouchNode.attrib['total'])
                            tipodocumento = vouchNode.attrib['tipodocumento']
                            
                            if tipodocumento != "I":
                                raise UserError(_('El archivo XML adjunto no es de tipo Ingreso [I]'))
                            else:
                                validacion = Validacion()
                                rfc_emisor = rfc_emisor
                                rfc_receptor = rfc_receptor                                
                                total = str(monto_total)
                                uuid = uuid
                                estado = validacion.obtener_estado(rfc_emisor, rfc_receptor, total, uuid)
                        if estado['estado'] != 'Vigente':
                            raise UserError(
                                    _('No Puede Validar la Factura o Nota de Credito, el SAT devolvió lo siguiente: .\n\n'
                                      'Codigo Estatus: %s\n'
                                      'Estado: %s\n\n'
                                      'Folio Fiscal: %s\n'
                                      'RFC Emisor: %s\n'
                                      'RFC Receptor: %s\n'
                                      'Monto Total: %d') % (estado['codigo_estatus'], estado['estado'], uuid, rfc_emisor, rfc_receptor, monto_total))
                        else:
                            
                            self.uuid_invoice = uuid

                        if not uuid:
                            raise UserError(_('Formato de archivo XML incorrecto\n\nSe necesita cargar un archivo de extensión ".xml" (CFDI)'))
                    rec.message_post(body=_("La factura (XML) adjunta se encuentra Vigente en el SAT\n%s"))
        return res

        
class HrExpense(models.Model):

    _inherit = "hr.expense"

    uuid_fact = fields.Char('UUID de Factura')
    
    def submit_expenses(self):
        if any(expense.state != 'draft' for expense in self):
            raise UserError(_("You cannot report twice the same line!"))
        if len(self.mapped('employee_id')) != 1:
            raise UserError(_("You cannot report expenses for different employees in the same report!"))
        adjunto_xml_id = self.env['ir.attachment'].search([('res_model', '=', 'hr.expense'), ('res_id', '=', self.id), ('name', 'ilike', '.xml')], limit=1)
        
        if adjunto_xml_id:
            uuid = False
            
            for att in adjunto_xml_id:
                xml_data = base64.b64decode(att.datas).replace(b'http://www.sat.gob.mx/cfd/3 ', b'').replace(b'TipoDeComprobante=',b'tipodocumento=').replace(b'Rfc=',b'rfc=').replace(b'Fecha=',b'fecha=').replace(b'Total=',b'total=').replace(b'Folio=',b'folio=').replace(b'Serie=',b'serie=')
                res = False
                
                xmlTree = et.ElementTree(et.fromstring(xml_data))
                vouchNode = xmlTree.getroot()
                uuid = vouchNode.find('{http://www.sat.gob.mx/cfd/3}Complemento').find('{http://www.sat.gob.mx/TimbreFiscalDigital}TimbreFiscalDigital').attrib['UUID'].upper()
                rfc_emisor = vouchNode.find('{http://www.sat.gob.mx/cfd/3}Emisor').attrib['rfc'].upper()
                rfc_receptor = vouchNode.find('{http://www.sat.gob.mx/cfd/3}Receptor').attrib['rfc'].upper()
                monto_total = float(vouchNode.attrib['total'])
                tipodocumento = vouchNode.attrib['tipodocumento']
                
                if tipodocumento != "I":
                    raise UserError(_('El archivo XML adjunto no es de tipo Ingreso [I]'))
                else:
                    validacion = Validacion()
                    rfc_emisor = rfc_emisor
                    rfc_receptor = rfc_receptor                                
                    total = str(monto_total)
                    uuid = uuid
                    estado = validacion.obtener_estado(rfc_emisor, rfc_receptor, total, uuid)
            if estado['estado'] != 'Vigente':
                raise UserError(
                        _('No Puede Validar la Factura o Nota de Credito, el SAT devolvió lo siguiente: .\n\n'
                          'Codigo Estatus: %s\n'
                          'Estado: %s\n\n'
                          'Folio Fiscal: %s\n'
                          'RFC Emisor: %s\n'
                          'RFC Receptor: %s\n'
                          'Monto Total: %d') % (estado['codigo_estatus'], estado['estado'], uuid, rfc_emisor, rfc_receptor, monto_total))
            else:
                self.uuid_fact = uuid           
        return {
            'type': 'ir.actions.act_window',
            'view_mode': 'form',
            'res_model': 'hr.expense.sheet',
            'target': 'current',
            'context': {
                'default_expense_line_ids': [line.id for line in self],
                'default_employee_id': self[0].employee_id.id,
                'default_name': self[0].name if len(self.ids) == 1 else ''
            }
        }
