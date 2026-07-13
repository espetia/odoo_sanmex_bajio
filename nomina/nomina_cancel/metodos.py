# -*- encoding: utf-8 -*-

from odoo import api, fields, models, _, release
from odoo.exceptions import UserError
from datetime import datetime, date, timedelta
from datetime import datetime
from odoo.exceptions import UserError, RedirectWarning, ValidationError
import time
import requests
import json
import urllib
import base64
import logging
_logger = logging.getLogger(__name__)

class HrPayslipCancela(models.Model):
    _inherit = 'hr.payslip'
      

    
    cancel_move_id = fields.Many2one('account.move', string='Póliza de Cancelación', readonly=True, index=True, 
                                      ondelete='restrict', copy=False,
                                      help="Liga a la póliza contable correspondiente a las partidas de cancelación.")
    cancel_solicitud = fields.Many2one('cancelaciones', string="Solicitud de Cancelación", readonly=True, copy=False)
    status_cancel = fields.Char(string='Estatus de Cancelación', readonly=True)

    @api.onchange('uuid_sustituye', 'cancelaciones_id')
    def _onchange_sustitucion(self):  
        _logger.info('dominio')
        if self.cancelaciones_id.code == '01':
            _logger.info('dominio1')   
            return {'domain': {'uuid_sustituye': [('fecha_factura','>=',self._context.get('date', fields.Date.context_today(self))), ('state','=','done'), ('employee_id','=', self.employee_id.id), ('cancel_solicitud','=',False)]}}

    cancelaciones_id = fields.Many2one('cancelaciones.cfdinuevo', string='Motivo de Cancelación', copy=False)
    uuid_sustituye = fields.Many2one('hr.payslip', string='Nómina Sustituta', copy=False)
    #@api.model
    def action_payslip_cancel_custom(self):
        _logger.info('funcion cancelar nomina')
        date = self._context.get('date', fields.Date.context_today(self))
        account_move_obj = self.env['account.move']             
        
        journal_id = self.env['account.journal'].search([('use_for_invoice_cancel','=', 1)], limit=1)        
       
        for nom in self:
            

            #    continue
            if nom:
                
                item_concept = 'item_concept' in ((nom.move_id._fields) or {}) and nom.move_id.item_concept or False
                default = { 'date'        : date,
                            'ref'         : _('Cancelación de Nómina ') + nom.number,
                            'journal_id'  : journal_id.id,
                            'type': 'entry',
                            }
                if item_concept:
                    default.update({'item_concept':item_concept})
                new_move = nom.move_id.copy_data(default=default)
                for line in new_move[0]['line_ids']:
                    line[2]['debit'], line[2]['credit'] = line[2]['credit'], line[2]['debit']
                    if line[2]['currency_id']:
                        line[2]['amount_currency'] = line[2]['amount_currency'] * -1
                    line[2]['move_id'] and line[2].pop('move_id')
                    #line[2]['tax_ids'] and line[2].pop('tax_ids')
                    line[2].update({'journal_id': journal_id.id})
                _logger.error('lineas: %s', line[2])
                move_id = account_move_obj.create(new_move[0])
                move_id.post()
                move_lines = self.env['account.move.line']
                move_line_invoice = nom.move_id.line_ids.filtered(lambda r: not r.reconciled) #and r.account_id.internal_type == 'receivable' and r.account_id.internal_type == 'payable')                
                move_line_cancel  = move_id.line_ids.filtered(lambda r: not r.reconciled) #and r.account_id.internal_type == 'receivable' and r.account_id.internal_type == 'payable')
                if 'complement_line_ids' in ((move_line_invoice._fields) or {}) and move_line_invoice.complement_line_ids:
                
                    default = {'move_line_id' : move_line_cancel.id}
                    for complemento in move_line_invoice.complement_line_ids:
                        res = complemento.copy(default=default)    
                #(move_line_invoice + move_line_cancel).reconcile(writeoff_acc_id=False, writeoff_journal_id=False)
                
                nom.write({'cancel_move_id': move_id.id})
                #inv.cancel_appply = True
        
            if self.folio_fiscal:# and self.status_cancel != 'Cancelado':
                raise UserError(_("No puedes crear póliza de reversión a una nómina con timbre (UUID).\n\nPrimero debes enviar una solicitud de cancelación del CFDI y esperar respuesta."))
           
        return super(HrPayslipCancela, self).action_payslip_cancel()
    
    def action_cfdi_cancel(self):
        for payslip in self:
            if payslip.nomina_cfdi:
                if payslip.estado_factura == 'factura_cancelada':
                    pass

                login = {}
                fname_xml = payslip.number and payslip.number + '.xml' or '' 
                webservice_url = self.env['ir.config_parameter'].sudo().get_param('webservice.url')
                webservice_url = self.env['ir.config_parameter'].sudo().get_param('webservice.url')
                multi_company = self.env['ir.config_parameter'].sudo().get_param('webservice.multi_company')
                if multi_company == False:           
                    login = {
                        "rfc": self.env['ir.config_parameter'].sudo().get_param('webservice.rfc_web'),
                        "clave": self.env['ir.config_parameter'].sudo().get_param('webservice.password')
                        }
                else:
                    _logger.info('condición aceptada')
                    login = {
                        "rfc": payslip.company_id.rfc_web_1,
                        "clave": payslip.company_id.password_1
                        }
                if webservice_url == 'test':
                    url = self.env['ir.config_parameter'].sudo().get_param('webservice.url_name_prue')
                if webservice_url == 'product':
                    url = self.env['ir.config_parameter'].sudo().get_param('webservice.url_name_produc')
                  
                if self.cancelaciones_id.code == '01':
                    if not self.uuid_sustituye:
                        raise UserError(_("Debes seleccionar la Factura que sustituye el CFDI a cancelar")) 
                if self.cancelaciones_id.code != '01':
                    data = {
                              "Login": login,
                              "FoliosUUID": {
                              "FolioUUID": [
                              {
                              "UUID": '|'+self.folio_fiscal +'|'+self.cancelaciones_id.code+'|'+'|'
                               
                              
                              }
                              ]
                              }
                              }
                else:
                    data = {
                              "Login": login,
                              "FoliosUUID": {
                              "FolioUUID": [
                              {
                              "UUID": '|'+self.folio_fiscal +'|'+self.cancelaciones_id.code+'|'+self.uuid_sustituye.folio_fiscal+'|'
                              
                              }
                              ]
                              }
                              }
                _logger.error("Cancelación: %s", data)
                headers =  {'content-type': 'application/json','timeout':'500000'}
                Respuesta =  requests.post(str(url) + "/v2/cfdi/cancela", data=json.dumps(data), headers=headers)                
                consulta =  json.loads(Respuesta.content.decode("utf-8"))
                _logger.error('consultas: %s', consulta)
                ad = dict()
                xml_recep = ""

                if consulta['Codigo'] == 1: 
                    ad['type_document'] = "Nómina"
                    ad['fecha_timbrado'] = payslip.fecha_factura
                    ad['cfdi_num_certificado'] = payslip.company_id.serial_number
                    #ad['cfdi_sello'] = self.selo_sat
                    ad['cfdi_folio'] = self.folio_fiscal
                    #ad['cfdi_cadena_original'] = self.cadena_origenal
                    ad['pac_timbrado'] = "SIFEI"
                    ad['sello'] = ""
                    ad['certificado'] = ""
                    ad['total_docto'] = self.total_nomina
                    #ad['factura'] = self.id
                    ad['rfc_emisor'] = payslip.company_id.rfc
                    ad['rfc_receptor'] = payslip.employee_id.rfc           
                    ad['fecha_cancelacion'] = consulta['Data']['Cancela']['Acuse']["fecha"]
                    ad["rfemisior"] = consulta['Data']['Cancela']['Acuse']["RefEmisor"]
                    ad["folio_cancelacion"] = consulta['Data']['Cancela']['Acuse']["FolioCancelacion"] 
                    ad['codigo_solicitud'] = consulta['Data']['Cancela']['Acuse']["EstatusUUID"]  
                    xml_recep = consulta['Data']['Cancela']['Acuse']["XmlBase64"]             
                      
                    result = self.env['cancelaciones'].create(ad)
                    self.cfdi_fecha_cancelacion = consulta['Data']['Cancela']['Acuse']["fecha"]
                    self.cancel_solicitud = result.id
                    xml_dec = base64.decodestring(str.encode(xml_recep))            
                    xml_dec= xml_dec.decode("utf-8").replace('\r\n','') 
                    _logger.error('Xml: %s', xml_dec)
                    attachment_obj = self.env['ir.attachment']   
                      
                    data_at = {
                                  'name': fname_xml,
                                  'datas': base64.encodestring(str.encode(xml_dec)),                          
                                  'description': 'Archivo XML del Acuse de solicitud de cancelación',
                                  'res_model': 'cancelaciones',
                                  'res_id': result.id,
                                  'type': 'binary',                        
                      }
                    _logger.error('Adjunto: %s', data_at)
                    attach = attachment_obj.with_context({}).create(data_at)

                    xres = self.with_context(cancelacion = True).do_something_with_xml_attachment(attach)
                self.env.cr.commit()
                return True

    
class AccountPayslipCancel(models.TransientModel):
    _name = "nomina.cancel_wizard"
    
    #@api.model

    @api.model
    def _default_journal(self):
        return self.env['account.journal'].search([('use_for_invoice_cancel','=', 1)], limit=1)

    
    
    date = fields.Date(string='Fecha Cancelación', default=fields.Date.context_today, required=True, readonly=False,
                        help="Fecha en la que se creará la Póliza de Cancelación de la Ńómina.")
    journal_id = fields.Many2one('account.journal', string='Diario', required=True, default=_default_journal, readonly=True)

    def action_payslip_cancel_wizard(self):
        self.ensure_one()
        
        active_ids = self._context.get('active_ids', []) or []
        _logger.error('active_ids: %s', active_ids)
        if not self.journal_id:

            raise UserError(_("No tiene configurado el Diario Contable a utilizarse cuando se haga Cancelación de Nómina.\n\nEsto lo puede realizar en el la vista de Formulario del Diario Contable."))
          
        #for active in active_ids:
        self.env['hr.payslip'].browse(active_ids).action_payslip_cancel_custom()
        return {'type': 'ir.actions.act_window_close'}
    