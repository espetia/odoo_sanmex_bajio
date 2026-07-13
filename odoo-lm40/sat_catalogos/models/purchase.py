# -*- encoding: utf-8 -*-

from odoo import api, fields, models, _
#import xmltodict
import base64
from xml.dom.minidom import parse, parseString
from odoo.exceptions import UserError, ValidationError
from lxml import etree as et
import requests
import json
import urllib
import logging
_logger = logging.getLogger(__name__)

class PurchaseOrder(models.Model):
    _inherit = 'purchase.order'

    READONLY_STATES = {
        'purchase': [('readonly', True)],
        'done': [('readonly', True)],
        'cancel': [('readonly', True)],
    }

    @api.onchange('partner_id', 'company_id')
    def onchange_partner_id(self):
        res = super(PurchaseOrder, self).onchange_partner_id()
        if self.partner_id:
            bank_partner_id = self.env['res.partner.bank'].search([('partner_id', '=', self.partner_id.parent_id and self.partner_id.parent_id.id or self.partner_id.id)])
            if bank_partner_id:
                self.acc_payment = bank_partner_id[0].id or False
            self.pay_method_id = (self.partner_id.parent_id and self.partner_id.parent_id.pay_method_id) or \
                                 (self.partner_id.pay_method_id and self.partner_id.pay_method_id) or False
        return res


    acc_payment = fields.Many2one('res.partner.bank', string='Cuenta Bancaria',
                                readonly=True, states={'draft': [('readonly', False)]})
    pay_method_id = fields.Many2one('pay.method', string='Forma de Pago',
                                readonly=True, states={'draft': [('readonly', False)]})
    partner_id = fields.Many2one('res.partner', string='Vendor', required=True, states=READONLY_STATES, change_default=True, tracking=True, domain="[('supplier','=', True)]", help="You can find a vendor by its Name, TIN, Email or Internal Reference.")
        
        

class invoice_diot(models.Model):
    _inherit = 'account.move'

    
    valida_nosat  = fields.Boolean(string='Validar sin XML', track_visibility='onchange')
    fact_extranjera = fields.Char(string='No. factura extranjera', size=36, readonly=True, states={'draft': [('readonly', False)]})                                     
    uuid_factura = fields.Char('UUID de factura', readonly=True)
    
    #@api.model
    def action_move_create(self):
        ### Codigo para validar si es Ingreso Credito o de Contado
        #account_move = self.env['account.move']
        for invoice in self:
            if not invoice.amount_total:
                continue
            plazo_pagos = self.env['account.payment.term']
            lineas_factura = self.env['account.move.line']
            if invoice.move_type == 'out_invoice':
                for line in invoice.invoice_line_ids:
                    # Validacion para contabilizar Ingreso a Credito o Contado (segun tenga configurada la cuenta la categoria del producto y/o el producto)
                    if line.product_id and line.account_id.id in (line.product_id.property_account_income_id.id, line.product_id.account_income.id,line.product_id.categ_id.property_account_income_categ_id.id,line.product_id.categ_id.account_income.id):
                        new_account = bool(invoice.date_invoice == invoice.date_due) and \
                                          (line.product_id.account_income.id or line.product_id.categ_id.account_income.id) or \
                                          (line.product_id.property_account_income_id.id or line.product_id.categ_id.property_account_income_categ_id.id)
                        if new_account and line.account_id.id != new_account:
                            line.write({'account_id': new_account})
                    ### Fin de Codigo para validar si es Ingreso Credito o de Contado
        
        # Continuación código original
        complements = self.env['eaccount.complements']
        complements_type_id = self.env['eaccount.complement.types'].search([('key', '=', 'foreign')], limit=1)
        #move = account_move.create(move_vals)
        super(invoice_diot, self).action_move_create()
        #company = self.env.user.company_id
        #res.post()
        
        company = self.env.user.company_id
        if not company.auto_mode_enabled:
            return True
        for inv in self:
            if not inv.amount_total:
                continue
            line_id = []
            if inv.move_type not in ('in_invoice', 'in_refund'):
                continue
            if inv.move_type == 'in_invoice':
                line_id = [ ln.id for ln in inv.move_id.line_ids if ln.account_id.internal_type == 'payable' ]
                msg = u'No se encontró ningún asiento con una cuenta de tipo "A pagar" en la póliza %s' % inv.move_id.name
            else:
                line_id = [ ln.id for ln in inv.move_id.line_ids ]
                msg = u'No se encontraron asientos en la poliza %s' % str(inv.move_id.name)
            if not line_id:
                msg = u'No se encontraron asientos en la poliza %s' % str(inv.move_id.name)
                raise UserError(_('Información faltante\n\n %s') % (msg))
            cmpl_vals = {}
            partner = inv.partner_id.parent_id or inv.partner_id
            if partner.tipo_tercero == '05' and not partner.nif_diot:
                raise UserError(_('Información faltante\n\nSe necesita un ID fiscal para el complemento a extranjeros, verifique la configuración de la DIOT para este proveedor.'))
            cmpl_vals['foreign_taxid'] = partner.nif_diot
            cmpl_vals['fact_extranjera'] = inv.reference
            if cmpl_vals['foreign_taxid'] and cmpl_vals['fact_extranjera']:
                cmpl_vals.update({'amount'          : inv.amount_total,
                                 'compl_date'       : inv.date_invoice,
                                 'compl_currency_id': inv.currency_id.id,
                                 'type_key'         : 'foreign',
                                 'type_id'          : complements_type_id.id,
                                 'move_line_id'     : line_id[0]
                                 })
                curr_rate = False
                rate_lines = [ rate for rate in inv.currency_id.rate_ids if rate.name == inv.date_invoice ]
                if len(rate_lines) and rate_lines[0].rate:
                    curr_rate = 1 / rate_lines[0].rate
                else:
                    rate_lines = [{'name':val.name,'rate':val.rate} for val in inv.currency_id.rate_ids]                    
                    for ln in rate_lines:
                        if ln['name'] < inv.date_invoice and ln['rate']:
                            curr_rate = 1 / ln['rate']
                            break                
                    

                cmpl_vals['exchange_rate'] = str(curr_rate) if curr_rate else False
                compl_rec = complements.create(cmpl_vals)
            else:
                attachment = self.env['ir.attachment'].search([('name', 'ilike', '.xml'), ('res_model', '=', 'account.move'), ('res_id', '=', inv.id)], limit=1)
                if attachment:
                    cmplObj = self.env['eaccount.complements']
                    user = self.env.user
                    cmpl_vals = cmplObj.onchange_attached(attachment=attachment.datas, currency_id=inv.currency_id)['value']
                    if not partner.rfc:
                        raise UserError(_('Información faltante\n\nEl proveedor %s no tiene configurado un R.F.C.') % partner.name)
                    partner_rfc = partner.rfc[2:] if len(partner.rfc) > 13 else partner.rfc
                    if partner.tipo_tercero == '04' and partner_rfc != partner.rfc:
                        raise UserError(_('Inconsistencia de datos.\n\nEl RFC emisor ("%s") no coincide con el RFC del proveedor ("%s")') % (partner.rfc, partner_vat))
                    if user.company_id.rfc != cmpl_vals['rfc2']:
                        raise UserError(_('Inconsistencia de datos\n\nEl RFC receptor ("%s") no coincide con el RFC de la empresa ("%s")') % (cmpl_vals['rfc2'], user.company_id.rfc))
                    parameter = float(self.env['ir.config_parameter'].get_param('rango_entre_registro_factura_y_xmlcfdi')) or 0
                    low = inv.amount_total - parameter
                    upp = inv.amount_total + parameter
                    if not low < cmpl_vals['amount'] < upp:
                        raise UserError(_('Inconsistencia de datos\n\nEl total del XML (%f) está fuera del rango de tolerancia de +/- %f') % (cmpl_vals['amount'], parameter))
                    cmpl_vals['type_id'] = self.env['eaccount.complement.types'].search([('key', '=', 'cfdi')], limit=1).id
                    cmpl_vals['type_key'] = 'cfdi'
                    cmpl_vals['move_line_id'] = line_id[0]
                    cmplObj.create(cmpl_vals)
            inv.move_id.write({'item_concept': company._assembly_concept(inv.move_type, invoice=inv)})
        return True
                                

    #@api.model
    def action_post(self):
        
        _logger.info('pruebas')
        res = super(invoice_diot, self).action_post()
        webservice_url = self.env['ir.config_parameter'].sudo().get_param('webservice.url')
        if webservice_url == 'test':
            url = self.env['ir.config_parameter'].sudo().get_param('webservice.url_name_prue')
        if webservice_url == 'product':
            url = self.env['ir.config_parameter'].sudo().get_param('webservice.url_name_produc')
        #_logger.info('en función')
        for rec in self:
            

            if rec.move_type in ('in_invoice','in_refund'):

                if rec.valida_nosat == False:
                   
                    adjunto_xml_id = self.env['ir.attachment'].search([('res_model', '=', 'account.move'), ('res_id', '=', rec.id), ('name', 'ilike', '.xml')], limit=1)
                    _logger.error('adjunto_xml_id: %s', adjunto_xml_id)
                    if not adjunto_xml_id:
                        raise UserError(_('No Puede Validar la Factura o Nota de Credito sin el archivo XML...'))
                    elif adjunto_xml_id:
                        uuid = False
                        
                        for att in adjunto_xml_id:
                            _logger.info('en función')
                            xml_data_registro = base64.b64decode(att.datas).replace(b'http://www.sat.gob.mx/registrofiscal ', b'').replace(b'TipoDeComprobante=',b'tipodocumento=').replace(b'Rfc=',b'rfc=').replace(b'Fecha=',b'fecha=').replace(b'Total=',b'total=').replace(b'Folio=',b'folio=').replace(b'Serie=',b'serie=') or base64.b64decode(att.datas).replace(b'http://www.sat.gob.mx/cfd/3 ', b'').replace(b'TipoDeComprobante=',b'tipodocumento=').replace(b'Rfc=',b'rfc=').replace(b'Fecha=',b'fecha=').replace(b'Total=',b'total=').replace(b'Folio=',b'folio=').replace(b'Serie=',b'serie=')
                            xml_data = base64.b64decode(att.datas).replace(b'http://www.sat.gob.mx/registrofiscal ', b'').replace(b'TipoDeComprobante=',b'tipodocumento=').replace(b'Rfc=',b'rfc=').replace(b'Fecha=',b'fecha=').replace(b'Total=',b'total=').replace(b'Folio=',b'folio=').replace(b'Serie=',b'serie=') or base64.b64decode(att.datas).replace(b'http://www.sat.gob.mx/cfd/4 ', b'').replace(b'TipoDeComprobante=',b'tipodocumento=').replace(b'Rfc=',b'rfc=').replace(b'Fecha=',b'fecha=').replace(b'Total=',b'total=').replace(b'Folio=',b'folio=').replace(b'Serie=',b'serie=')
                            res = False
                            
                            xmlTree_v = et.ElementTree(et.fromstring(xml_data_registro))
                            vouchNode_v = xmlTree_v.getroot()
                            _logger.error('versión: %s', vouchNode_v.attrib['Version'])
                            xmlTree_v4 = et.ElementTree(et.fromstring(xml_data))
                            vouchNode_v4 = xmlTree_v4.getroot()

                            if vouchNode_v.attrib['Version'] == '3.3':
                                _logger.info('cfd3')
                                xmlTree = et.ElementTree(et.fromstring(xml_data_registro))
                                vouchNode = xmlTree.getroot()
                                uuid = vouchNode.find('{http://www.sat.gob.mx/cfd/3}Complemento').find('{http://www.sat.gob.mx/TimbreFiscalDigital}TimbreFiscalDigital').attrib['UUID'].upper() 
                                rfc_emisor = vouchNode.find('{http://www.sat.gob.mx/cfd/3}Emisor').attrib['rfc'].upper() or vouchNode_4.find('{http://www.sat.gob.mx/cfd/4}Emisor').attrib['rfc'].upper()
                                rfc_receptor = vouchNode.find('{http://www.sat.gob.mx/cfd/3}Receptor').attrib['rfc'].upper() or vouchNode_4.find('{http://www.sat.gob.mx/cfd/3}Receptor').attrib['rfc'].upper()
                                monto_total = float(vouchNode_v.attrib['total'])
                                _logger.error('monto: %s', monto_total)
                                tipodocumento = vouchNode.attrib['tipodocumento']
                            if vouchNode_v.attrib['Version'] == '4.0':
                                _logger.info('cfd4')
                                xmlTree = et.ElementTree(et.fromstring(xml_data))
                                vouchNode = xmlTree.getroot()
                                _logger.info('nohay nada')                               
                                uuid = vouchNode.find('{http://www.sat.gob.mx/cfd/4}Complemento').find('{http://www.sat.gob.mx/TimbreFiscalDigital}TimbreFiscalDigital').attrib['UUID'].upper()
                                rfc_emisor = vouchNode.find('{http://www.sat.gob.mx/cfd/4}Emisor').attrib['rfc'].upper()
                                rfc_receptor = vouchNode.find('{http://www.sat.gob.mx/cfd/4}Receptor').attrib['rfc'].upper()
                                monto_total = float(vouchNode.attrib['total'])
                                _logger.error('monto: %s', monto_total)
                                tipodocumento = vouchNode.attrib['tipodocumento']
                            _logger.error('uui: %s', uuid)
                            
                            
                          
                            #_logger.error('tipodocumento: %s', tipodocumento)
                            if tipodocumento != "I":
                                raise UserError(_('El archivo XML adjunto no es de tipo Ingreso [I]'))
                            else:
                                data = {
                                        "uuid": uuid,
                                        "receptor": rfc_receptor,
                                        "emisor": rfc_emisor,
                                        "total": monto_total
                                    }  
                                _logger.error("datos validados: %s", data)  
                                headers =  {'content-type': 'application/json','timeout':'500000'}
                                Respuesta =  requests.post(str(url) + "/Consulta/Estado", data=json.dumps(data), headers=headers)                
                                consulta =  json.loads(Respuesta.content.decode("utf-8"))
                                _logger.error('consultas: %s', consulta)
                            
                        if consulta['Estado'] != 'Vigente':
                            raise UserError(
                                    _('No Puede Validar la Factura o Nota de Credito, el SAT devolvió lo siguiente: .\n\n'
                                      'Codigo Estatus: %s\n'
                                      'Estado: %s\n\n'
                                      'Folio Fiscal: %s\n'
                                      'RFC Emisor: %s\n'
                                      'RFC Receptor: %s\n'
                                      'Monto Total: %d') % (consulta['CodigoEstatus'], consulta['Estado'], uuid, rfc_emisor, rfc_receptor, monto_total))
                        else:
                            ad = dict()
                            ad['name'] = self.id
                            ad['partner_id'] = self.partner_id.name
                            ad['fecha_creacion'] = self.invoice_date
                            ad['UUID'] = uuid
                            ad['estado_factura'] = consulta['Estado']
                            ad['rfc_receptor'] = rfc_receptor
                            ad['rfc_emisor'] = rfc_emisor
                            ad['monto_total'] = monto_total
                            ad['currency_id'] = self.currency_id.id
                            self.env['registro.invoice'].create(ad)
                            self.uuid_factura = uuid
                            
                            complements = self.env['eaccount.complements']
                            complements_type_id = self.env['eaccount.complement.types'].search([('key', '=', 'foreign')], limit=1)
                            #move = account_move.create(move_vals)
                            #super(invoice_diot, self).action_move_create()
                            #company = self.env.user.company_id
                            #res.post()
                            
                            company = self.env.user.company_id
                            if not company.auto_mode_enabled:
                                return True
                            for inv in self:
                                if not inv.amount_total:
                                    continue
                                line_id = []
                                if inv.move_type not in ('in_invoice', 'in_refund'):
                                    continue
                                if inv.move_type == 'in_invoice':
                                    line_id = [ ln.id for ln in inv.line_ids if ln.account_id.internal_type == 'payable' ]
                                    msg = u'No se encontró ningún asiento con una cuenta de tipo "A pagar" en la póliza %s' % inv.name
                                else:
                                    line_id = [ ln.id for ln in inv.line_ids ]
                                    msg = u'No se encontraron asientos en la poliza %s' % str(inv.name)
                                if not line_id:
                                    msg = u'No se encontraron asientos en la poliza %s' % str(inv.name)
                                    raise UserError(_('Información faltante\n\n %s') % (msg))
                                cmpl_vals = {}
                                partner = inv.partner_id.parent_id or inv.partner_id
                                if partner.tipo_tercero == '05' and not partner.nif_diot:
                                    raise UserError(_('Información faltante\n\nSe necesita un ID fiscal para el complemento a extranjeros, verifique la configuración de la DIOT para este proveedor.'))
                                cmpl_vals['foreign_taxid'] = partner.nif_diot
                                cmpl_vals['fact_extranjera'] = inv.ref
                                if cmpl_vals['foreign_taxid'] and cmpl_vals['fact_extranjera']:
                                    cmpl_vals.update({'amount'          : inv.amount_total,
                                                     'compl_date'       : inv.invoice_date,
                                                     'compl_currency_id': inv.currency_id.id,
                                                     'type_key'         : 'foreign',
                                                     'type_id'          : complements_type_id.id,
                                                     'move_line_id'     : line_id[0]
                                                     })
                                    curr_rate = False
                                    rate_lines = [ rate for rate in inv.currency_id.rate_ids if rate.name == inv.invoice_date ]
                                    if len(rate_lines) and rate_lines[0].rate:
                                        curr_rate = 1 / rate_lines[0].rate
                                    else:
                                        rate_lines = [{'name':val.name,'rate':val.rate} for val in inv.currency_id.rate_ids]                    
                                        for ln in rate_lines:
                                            if ln['name'] < inv.date_invoice and ln['rate']:
                                                curr_rate = 1 / ln['rate']
                                                break                
                                        

                                    cmpl_vals['exchange_rate'] = str(curr_rate) if curr_rate else False
                                    compl_rec = complements.create(cmpl_vals)
                                else:
                                    attachment = self.env['ir.attachment'].search([('name', 'ilike', '.xml'), ('res_model', '=', 'account.move'), ('res_id', '=', inv.id)], limit=1)
                                    if attachment:
                                        cmplObj = self.env['eaccount.complements']
                                        user = self.env.user
                                        cmpl_vals = cmplObj.onchange_attached(attachment=attachment.datas, currency_id=inv.currency_id)['value']
                                        if not partner.rfc:
                                            raise UserError(_('Información faltante\n\nEl proveedor %s no tiene configurado un R.F.C.') % partner.name)
                                        partner_rfc = partner.rfc[2:] if len(partner.rfc) > 13 else partner.rfc
                                        if partner.tipo_tercero == '04' and partner_rfc != partner.rfc:
                                            raise UserError(_('Inconsistencia de datos.\n\nEl RFC emisor ("%s") no coincide con el RFC del proveedor ("%s")') % (partner.rfc, partner_vat))
                                        if user.company_id.rfc != cmpl_vals['rfc2']:
                                            raise UserError(_('Inconsistencia de datos\n\nEl RFC receptor ("%s") no coincide con el RFC de la empresa ("%s")') % (cmpl_vals['rfc2'], user.company_id.rfc))
                                        parameter = float(self.env['ir.config_parameter'].get_param('rango_entre_registro_factura_y_xmlcfdi')) or 0
                                        low = inv.amount_total - parameter
                                        upp = inv.amount_total + parameter
                                        """if not low < cmpl_vals['amount'] < upp:
                                            raise UserError(_('Inconsistencia de datos\n\nEl total del XML (%f) está fuera del rango de tolerancia de +/- %f') % (cmpl_vals['amount'], parameter))"""
                                        cmpl_vals['type_id'] = self.env['eaccount.complement.types'].search([('key', '=', 'cfdi')], limit=1).id
                                        cmpl_vals['type_key'] = 'cfdi'
                                        cmpl_vals['move_line_id'] = line_id[0]
                                        cmplObj.create(cmpl_vals)
                                inv.write({'item_concept': company._assembly_concept(inv.move_type, invoice=inv)})

                        if not uuid:
                            raise UserError(_('Formato de archivo XML incorrecto\n\nSe necesita cargar un archivo de extensión ".xml" (CFDI)'))
                    rec.message_post(body=_("La factura (XML) adjunta se encuentra Vigente en el SAT\n%s"))
        #return True
        
        return res
invoice_diot()

class Registro_pagos(models.Model):
    _name = 'registro.invoice'

    name = fields.Many2one('account.move', 'Numero de Factura', readonly=True)
    partner_id = fields.Char('Proveedor', readonly=True)
    UUID = fields.Char('UUID', readonly=True)
    estado_factura = fields.Char('Estado SAT', readonly=True)
    monto_total = fields.Monetary('Total Factura', readonly=True)
    currency_id = fields.Many2one('res.currency', string='Moneda', required=False, readonly=True,
        default=lambda self: self.env.user.company_id.currency_id.id)
    rfc_emisor = fields.Char('RFC Emisor', readonly=True)
    rfc_receptor = fields.Char('RFC Receptor', readonly=True)
    fecha_creacion = fields.Date('Fecha de creación', readonly=True)