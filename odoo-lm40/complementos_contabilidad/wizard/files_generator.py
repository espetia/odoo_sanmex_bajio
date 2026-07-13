# -*- encoding: utf-8 -*-
#
import sys
if sys.version_info[0] >= 3:
    unicode = str
from odoo import api, fields, models, _, tools
from odoo.exceptions import UserError, ValidationError
from base64 import b64decode as b64dec, b64encode as b64enc
from lxml import etree as et
from zipfile import ZipFile
import requests
import json
import urllib
import time
import os
import zipfile
import tempfile
import re
import base64
import lxml.etree
import calendar
import datetime
#import date
from xml.dom.minidom import parse, parseString
import logging
_logger = logging.getLogger(__name__)

_RFC_PATTERN = re.compile('[A-Z\xc3\x91&]{3,4}[0-9]{2}[0-1][0-9][0-3][0-9][A-Z0-9]?[A-Z0-9]?[0-9A-Z]?')
_SERIES_PATTERN = re.compile('[A-Z]+')
_UUID_PATTERN = re.compile('[a-f0-9A-F]{8}-[a-f0-9A-F]{4}-[a-f0-9A-F]{4}-[a-f0-9A-F]{4}-[a-f0-9A-F]{12}')

class files_generator_wizard(models.TransientModel):
    _name = 'files.generator.wizard'
    
    filename    = fields.Char(string='Archivo', size=128)
    primary_file= fields.Binary(string='Archivo Plano', filename="filename")
    stamped_file= fields.Binary(string='Archivo Sellado')
    zipped_file = fields.Binary(string='Archivo Zipped')
    format      = fields.Selection([('xml', 'XML')], string='Formato del archivo', 
                                    required=True, default='xml')
    xml_target  = fields.Selection([
                                    ('accounts_catalog', 'Catálogo de cuentas'),
                                    ('trial_balance', 'Balanza de comprobación'),
                                    ('vouchers', 'Información de pólizas'),
                                    ('helpers', 'Auxiliar de folios'),
                                    ('helpers_account', 'Auxiliar de cuentas y sub-cuentas')], 
                                    string='Archivo a generar', required=True, defaut='accounts_catalog')
    state  = fields.Selection([('init', 'Init'),
                               ('val_xcpt', 'Val Except'),
                               ('val_done', 'Val Done'),
                               ('stamp_xcpt', 'Stamp Except'),
                               ('stamp_done', 'Stamp Done'),
                               ('zip_done', 'Zip done')], string='State', default='init')
    month  = fields.Selection([('01', 'Enero'),
                               ('02', 'Febrero'),
                               ('03', 'Marzo'),
                               ('04', 'Abril'),
                               ('05', 'Mayo'),
                               ('06', 'Junio'),
                               ('07', 'Julio'),
                               ('08', 'Agosto'),
                               ('09', 'Septiembre'),
                               ('10', 'Octubre'),
                               ('11', 'Noviembre'),
                               ('12', 'Diciembre'),
                               ('13', '-- Cierre --')], string='Periodo', required=True)
    trial_delivery  = fields.Selection([('N', 'Normal'), ('C', 'Complementaria')], 
                                       string='Tipo de envío', required=True, default='N')
    trial_lastchange_date = fields.Date('Última modificación contable')
    request_type  = fields.Selection([('AF', 'Acto de fiscalización'),
                                      ('FC', 'Fiscalización compulsa'),
                                      ('DE', 'Devolución'),
                                      ('CO', 'Compensación')], string='Tipo de solicitud',  default=lambda *a: 'DE',
                                     attrs={'required': [('xml_target', '=', 'vouchers')]})
    order_number    = fields.Char(string='Número de orden', size=13)
    procedure_number= fields.Char(string='Número de trámite', size=14) # Cambio Contabilidad 1.3
    year            = fields.Integer(string='Ejercicio', required=True, default=lambda *a: int(time.strftime('%Y')))
    accounts_chart  = fields.Many2one('account.account', string='Plan contable', domain=[('parent_id', '=', False)])
    is_tamp = fields.Boolean(string='Sellar')   
   
    

    _LETTER_PERIODS = {'01': 'Enero / ',
     '02': 'Febrero / ',
     '03': 'Marzo / ',
     '04': 'Abril / ',
     '05': 'Mayo / ',
     '06': 'Junio / ',
     '07': 'Julio / ',
     '08': 'Agosto / ',
     '09': 'Septiembre / ',
     '10': 'Octubre / ',
     '11': 'Noviembre / ',
     '12': 'Diciembre / '}


    def _outputXml(self, output):
        return et.tostring(output, pretty_print=True, xml_declaration=True, encoding='UTF-8')


    def _reopen_wizard(self, res_id):
        return {'type'      : 'ir.actions.act_window',
                'res_id'    : res_id,
                'view_mode' : 'form',
                'view_type' : 'form',
                'res_model' : 'files.generator.wizard',
                'target'    : 'new',
                'name'      : 'Contabilidad electrónica'}    
    


    def _find_file_in_addons(self, directory, filename):
        """To use this method, specify a filename and the directory where it resides.
        Said directory must be at the first level for the modules folders."""
        addons_paths = tools.config['addons_path'].split(',')
        actual_module = directory.split('/')[0]
        if len(addons_paths) == 1:
            return os.path.join(addons_paths[0], directory, filename)
        for pth in addons_paths:
            for subdir in os.listdir(pth):
                if subdir == actual_module:
                    return os.path.join(pth, directory, filename)


        return False

    @api.model
    def do_something_with_xml_attachment(self, attach):

        return True

    
    #@api.model
    def process_file(self, account_ids = None, balance_ids = None, moveIds = None, auxiliar_ids=None):
        webservice_url = self.env['ir.config_parameter'].sudo().get_param('webservice.url')
        if webservice_url == 'test':
            url = self.env['ir.config_parameter'].sudo().get_param('webservice.url_name_prue')
        if webservice_url == 'product':
            url = self.env['ir.config_parameter'].sudo().get_param('webservice.url_name_produc')
        
        #self.ensure_one() 

        form = self
        user = self.env.user
        if len(user.company_id.rfc) < 12 or len(user.company_id.rfc) > 13 or not _RFC_PATTERN.match(user.company_id.rfc):
            raise UserError(_('Datos de compañia erróneos\n\nEl RFC "%s" no es válido con respecto a los lineamientos del SAT.') % (user.company_id.rfc))
        if form.year < 2015:
            raise UserError(_('Fecha fuera de rango\n\nLa contabilidad electrónica comienza a reportarse a partir del 2015.'))
        if not user.company_id.rfc:
            raise UserError(_('Información faltante\n\nNo se ha configurado un R.F.C. para la empresa'))
        periodObj = self.env['account.period']
        period_id = periodObj.search([('code', '=', form.month + '/' + str(form.year)), ('company_id', '=', user.company_id.id)], limit=1)
        _logger.error('fecha: %s', period_id.date_start)
        if form.xml_target == 'accounts_catalog':
            filename = self.env.user.company_id.rfc + str(period_id.date_start)[0:4] + str(period_id.date_start)[5:7] + 'CT' + '.xml'
        if form.xml_target == 'trial_balance':               
            filename = self.env.user.company_id.rfc + str(period_id.date_start)[0:4] + str(period_id.date_start)[5:7] + 'BN' + '.xml'  
        if not period_id:
            raise UserError(_('Información faltante\n\nEl periodo especificado no fue encontrado. Compruebe que los códigos de sus periodos fiscales tienen el formato "mm/aaaa"'))        
        if form.xml_target == 'accounts_catalog':
            catCtas_wizard_obj = self.env['catalogo.cuentas.wizard']
            catCtas_wizard = catCtas_wizard_obj.create({'chart_account_id': form.accounts_chart.id})
            account_ids = catCtas_wizard.get_info()            
            ctas = []
            for acc in account_ids:
                if acc.sat_account_code and acc.account_id.first_period_id.date_start <= period_id.date_start:
                    ctaAttrs = [ ('CodAgrup', acc.sat_account_code),
                                 ('NumCta', acc.account_code[0:100]),
                                 ('Desc', acc.account_name[0:400]),
                                 ('Nivel', acc.account_level),
                                 ('Natur', acc.account_nature)]
                    if acc.parent_id:
                        ctaAttrs.append(('SubCtaDe', acc.parent_code[0:100]))
                    ctas.append(dict(ctaAttrs))   

            
            catalogo= {
                "localizacion-mx": {
                        "login": {
                          "rfc":self.env['ir.config_parameter'].sudo().get_param('webservice.rfc_web'),
                          "clave":self.env['ir.config_parameter'].sudo().get_param('webservice.password')
                        }, 
                  "Catalogo": {
                    "Anio": str(period_id.date_start)[0:4],
                    "Mes": str(period_id.date_start)[5:7],
                    "RFC": user.company_id.rfc,
                    "Version": "1.3",
                    "Ctas": ctas                              
                  
                  }
                }
              }
            _logger.error('Datos: %s', catalogo)
            headers = {'content-type': 'application/json'}        
            res = requests.post(str(url) + "/ce/cuentas", data=json.dumps(catalogo), headers=headers)
            respuesta = json.loads(res.content.decode("utf-8"))
            
            ad = dict()
            if respuesta['Codigo'] == 1:
                ad['archivo_generado'] = "Catálogo de cuentas"
                ad['user_id'] = self.env.user.id
                ad['año_fiscal'] = str(period_id.date_start)[0:4]
                ad['periodo_declaracion'] = str(period_id.date_start)[5:7]
                xml_recep = respuesta['Data']['Cuentas']['xmlCuentas64']
                result = self.env['declaraciones.sat'].create(ad)
                xml_dec = base64.decodestring(str.encode(xml_recep))                           
                xml_dec= xml_dec.decode("utf-8").replace('\r\n','')
                

                self.write({
                            'filename': filename,                            
                            'primary_file': xml_recep
                            })

                attachment_obj = self.env['ir.attachment']   
          
                data_at = {
                            'name': filename,
                            'datas': base64.encodestring(str.encode(xml_dec)),                        
                            #'datas_fname': filename,
                            'description': 'Archivo XML declaracion',
                            'res_model': 'declaraciones.sat',
                            'res_id': result.id,
                            'type': 'binary',                        
                }
                _logger.error('Adjunto: %s', data_at)
                attach = attachment_obj.with_context({}).create(data_at)

                xres = self.do_something_with_xml_attachment(attach)
                
            else:
              raise UserError(_("Error: %s" % respuesta['Descripcion']))
            


        elif form.xml_target == 'trial_balance':
            if balance_ids is None:
                trialWizardObj = self.env['account.monthly_balance_wizard']                
                trial_balance_id = trialWizardObj.create({'chart_account_id': form.accounts_chart.id,
                                                         'company_id'       : user.company_id.id,
                                                         'period_id'        : period_id.id,
                                                         'partner_breakdown': False,
                                                         'output'           : 'list_view',})
                
                balance_ids = eval(trial_balance_id.get_info()['domain'][1:-1])[2]                
            balanceRecords = self.env['account.monthly_balance'].browse(balance_ids)            
            ctas = []
            for record in balanceRecords:
                if record.account_id.xml_report and record.account_id.first_period_id.date_start <= period_id.date_start: # and record.account_id.company_id.id == user.company_id.id:
                    ctasAttrs = [('NumCta', record.account_code[0:100]),
                                 ('SaldoIni', round(record.initial_balance, 2)),
                                 ('Debe', round(record.debit, 2)),
                                 ('Haber', round(record.credit, 2)),
                                 ('SaldoFin', round(record.ending_balance, 2))]
                    ctas.append(dict(ctasAttrs))            
            balanza = {
                      "localizacion-mx": {
                              "login": {
                                "rfc":self.env['ir.config_parameter'].sudo().get_param('webservice.rfc_web'),
                                "clave":self.env['ir.config_parameter'].sudo().get_param('webservice.password')
                              },
                        "Balanza": {
                          "Anio": str(period_id.date_start)[0:4],
                          "Mes": str(period_id.date_start)[5:7],
                          "RFC": user.company_id.rfc,
                          "TipoEnvio": form.trial_delivery,
                          "Version": '1.3',
                          "Ctas": ctas
                        }
                      }
                    }
            _logger.error("Balanza: %s", balanza)        
            headers = {'content-type': 'application/json'}        
            res = requests.post(str(url) + "/ce/balanza", data=json.dumps(balanza), headers=headers)
            respuesta = json.loads(res.content.decode("utf-8"))            
            ad = dict()
            if respuesta['Codigo'] == 1:
                ad['archivo_generado'] = "Balanza de Comprobación"
                ad['user_id'] = self.env.user.id
                xml_recep = respuesta['Data']['Balanza']['xmlBalanza64']
                result = self.env['declaraciones.sat'].create(ad)
                xml_dec = base64.decodestring(str.encode(xml_recep))                           
                xml_dec= xml_dec.decode("utf-8").replace('\r\n','')                
                self.write({
                            'filename': filename,                            
                            'primary_file': xml_recep
                            })
                attachment_obj = self.env['ir.attachment']   
          
                data_at = {
                            'name': filename,
                            'datas': base64.encodestring(str.encode(xml_dec)),                        
                            #'datas_fname': filename,
                            'description': 'Archivo XML declaracion',
                            'res_model': 'declaraciones.sat',
                            'res_id': result.id,
                            'type': 'binary',                        
                }
                
                attach = attachment_obj.with_context({}).create(data_at)

                xres = self.do_something_with_xml_attachment(attach)
            else:
              raise UserError(_("Error: %s" % respuesta['Descripcion']))

        elif form.xml_target in ('vouchers', 'helpers'):
            
            if form.request_type in ('AF', 'FC'):
                if len(form.order_number) != 13:
                    raise UserError(_('Número de orden erróneo\n\nVerifique que su número de orden contenga 13 caracteres (incluida la diagonal)'))
                if not re.compile('[A-Z]{3}[0-6][0-9][0-9]{5}(/)[0-9]{2}').match(form.order_number.upper()):
                    raise UserError(_('Número de orden erróneo\n\nVerifique que su número de orden tenga la siguiente estructura:\n  * Tres letras mayúsculas de la A al Z sin incluir la "Ñ"\n  * Un dígito entre 0 y 6\n  * Un dígito entre 0 y 9\n  * Cinco dígitos entre 0 y 9\n  * Una diagonal "/"\n  * Dos dígitos del entre 0 y 9'))
            if form.request_type in ('DE', 'CO'):
                if len(form.procedure_number) != 14:
                    raise UserError(_('Número de trámite erróneo\n\nVerifique que su número de trámite contenga 14 caracteres.'))
            accountMoveObj = self.env['account.move']
            if moveIds is None:            
                periods = periodObj.search([('name','=',period_id.name)]) # Esto es util para cuando se tienen Companys hijos
                period_ids = [w.id for w in periods]
                moves = accountMoveObj.search([('period_id', 'in', period_ids), ('state', '=', 'posted')]) #, ('company_id', '=', user.company_id.id)])
            else:
                moves = accountMoveObj.browse(moveIds)
            
            if not moves:
                raise UserError(_('Información faltante\n\nNo se han encontrado pólizas para el periodo seleccionado.'))
            entries = []
            if form.xml_target == 'vouchers':
                filename = self.env.user.company_id.rfc + str(form.year) + form.month 
        
                if form.xml_target == 'vouchers':
                    filename += 'PL' + '.xml'
                elif form.xml_target == 'helpers':
                    filename += 'XF' + '.xml'

                for mv in moves:
                    voucher = (mv.ref if mv.ref else '') + '(' + mv.name + ')'
                    if not mv.line_ids:
                        raise UserError(_('Póliza incompleta\n\nLa póliza %s no tiene asientos definidos.') % (voucher))
                    if not mv.item_concept and not mv.ref:
                        raise UserError(_('Información faltante\n\nLa póliza %s no tiene definido un concepto') % (voucher))

                    if not mv.item_concept:
                        mvAttrs = [('NumUnIdenPol', mv.name[0:50]), ('Fecha', mv.date), ('Concepto', mv.ref)]
                    else:
                        mvAttrs = [('NumUnIdenPol', mv.name[0:50]), ('Fecha', mv.date), ('Concepto', mv.item_concept[0:300])]
                    lines = []

                    for ln in mv.line_ids:
                        if not ln.name:
                            raise UserError(_('Información faltante\n\nCompruebe que todos los asientos de la póliza %s tengan un concepto definido.') % (voucher))
                        lnAttrs = [  ('NumCta', ln.account_id.code[0:100]),
                                     ('DesCta', ln.account_id.name[0:100]),
                                     ('Concepto', ln.name[0:200]),
                                     ('Debe', round(ln.debit, 2)),
                                     ('Haber', round(ln.credit, 2))]
                        (cfdis, others, foreigns, checks, transfers, payments,) = ([],
                         [],
                         [],
                         [],
                         [],
                         [])
                        for cmpl in ln.complement_line_ids:
                            if cmpl.rfc and not _RFC_PATTERN.match(cmpl.rfc):
                                raise UserError(_('Información incorrecta\n\nEl RFC "%s" no es válido con respecto a los lineamientos del SAT. Póliza %s') % (cmpl.rfc, voucher))
                            if cmpl.rfc2 and not _RFC_PATTERN.match(cmpl.rfc2):
                                raise UserError(_('Información incorrecta\n\nEl RFC "%s" no es válido con respecto a los lineamientos del SAT. Póliza %s') % (cmpl.rfc2, voucher))
                            cmpl_attrs = []
                            commons = ['cfdi', 'foreign', 'other']
                            cmpl_attrs.append(('MontoTotal' if cmpl.type_key in commons else 'Monto', round(cmpl.amount, 2)))
                            if cmpl.compl_currency_id:
                                if not cmpl.compl_currency_id.sat_currency_id:
                                    raise UserError(_('Información faltante\n\nLa moneda "%s" no tiene asignado un código del SAT.') % (cmpl.compl_currency_id.name))
                                cmpl_attrs.append(('Moneda', cmpl.compl_currency_id.sat_currency_id.code))
                            if cmpl.exchange_rate:
                                cmpl_attrs.append(('TipCamb', round(cmpl.exchange_rate, 5)))
                            commons.pop(1)
                            commons.append('check')
                            commons.append('transfer')
                            if cmpl.type_key in commons:
                                if cmpl.rfc and cmpl.rfc2 and cmpl.rfc != user.company_id.rfc and cmpl.rfc2 != user.company_id.rfc:
                                    cmpl_attrs.append(('RFC', cmpl.rfc2.upper()))
                                else:
                                    cmpl_attrs.append(('RFC', cmpl.rfc.upper() if cmpl.rfc != user.company_id.rfc else cmpl.rfc2.upper()))
                            commons.pop(0)
                            commons.pop(0)
                            if cmpl.type_key in commons:
                                if cmpl.show_native_accs and cmpl.origin_native_accid:
                                    cmpl_attrs.append(('CtaOri', cmpl.origin_native_accid.acc_number[0:50]))
                                elif cmpl.origin_account_id:
                                    cmpl_attrs.append(('CtaOri', cmpl.origin_account_id.acc_number[0:50]))
                            commons.append('payment')
                            if cmpl.type_key in commons:
                                cmpl_attrs.append(('Fecha', cmpl.compl_date))
                                cmpl_attrs.append(('Benef', cmpl.payee_acc_id.name[0:300] if cmpl.show_native_accs2 else cmpl.payee_id.name[0:300]))
                            if cmpl.type_key == 'cfdi':
                                if cmpl.uuid:
                                    if len(cmpl.uuid) != 36 or not _UUID_PATTERN.match(cmpl.uuid.upper()):
                                        raise UserError(_('Información incorrecta\n\nEl UUID "%s" en la póliza %s no se apega a los lineamientos del SAT.') % (cmpl.uuid, voucher))
                                    cmpl_attrs.append(('UUID_CFDI', cmpl.uuid.upper()))
                                cfdis.append(('CompNal', dict(cmpl_attrs)))
                            elif cmpl.type_key == 'other':
                                if cmpl.cbb_series and not _SERIES_PATTERN.match(cmpl.cbb_series):
                                    raise UserError(_('Información incorrecta\n\nLa "Serie" en el comprobante de la póliza %s solo debe contener letras.') % (voucher))
                                if cmpl.cbb_series:
                                    cmpl_attrs.append(('CFD_CBB_Serie', cmpl.cbb_series))
                                cmpl_attrs.append(('CFD_CBB_NumFol', cmpl.cbb_number))
                                others.append(('CompNalOtr', dict(cmpl_attrs)))
                            elif cmpl.type_key == 'foreign':
                                cmpl_attrs.append(('NumFactExt', cmpl.foreign_invoice))
                                cmpl_attrs.append(('TaxID', cmpl.foreign_taxid))
                                foreigns.append(('CompExt', dict(cmpl_attrs)))
                            elif cmpl.type_key == 'check':
                                if not cmpl.origin_bank_id:
                                    raise UserError(_('Información faltante\n\nEl Complemento en la Poliza %s no cuenta con la informacion del Banco Nacional Origen.') % (voucher)) # Contabilidad 1.3
                                if not cmpl.origin_bank_id.sat_bank_id.bic: # Contabilidad 1.3
                                    raise UserError(_('Información faltante\n\nNo se ha encontrado un número de identificacion Bancaria para el Banco % s') % (cmpl.origin_bank_id.name)) # Contabilidad 1.3

                                if not cmpl.check_number:
                                    raise UserError(_('Información faltante\n\nNo se ha encontrado un número de cheque en la póliza % s') % (voucher))
                                cmpl_attrs.append(('Num', cmpl.check_number))
                                cmpl_attrs.append(('BanEmisNal', cmpl.origin_bank_id.sat_bank_id.bic))
                                if cmpl.origin_bank_id.sat_bank_id.bic == '999':
                                    cmpl_attrs.append(('BanEmisExt', cmpl.origin_frgn_bank))
                                checks.append(('Cheque', dict(cmpl_attrs)))
                            elif cmpl.type_key == 'transfer':
                                if not cmpl.origin_bank_id:
                                    raise UserError(_('Información faltante\n\nEl Complemento en la Poliza %s no cuenta con la informacion del Banco Nacional Origen.') % (voucher)) # Contabilidad 1.3
                                if not cmpl.origin_bank_id.sat_bank_id.bic: # Contabilidad 1.3
                                    raise UserError(_('Información faltante\n\nNo se ha encontrado un número de identificacion Bancaria para el Banco %s') % (cmpl.origin_bank_id.name)) # Contabilidad 1.3
                                cmpl_attrs.append(('BancoOriNal', cmpl.origin_bank_id.sat_bank_id.bic))
                                if cmpl.origin_bank_id.sat_bank_id.bic == '999':
                                    cmpl_attrs.append(('BancoOriExt', cmpl.origin_bank_id.name[0:150]))
                                if not cmpl.destiny_native_accid.acc_number and not cmpl.destiny_account_id.acc_number:
                                    raise UserError(_('Información faltante\n\nLa Poliza %s no tiene una cuenta destino.') % (voucher))
                                cmpl_attrs.append(('CtaDest', cmpl.destiny_native_accid.acc_number[0:50] if cmpl.show_native_accs1 else cmpl.destiny_account_id.acc_number[0:50]))
                                if not cmpl.destiny_bank_id.sat_bank_id.bic:
                                    raise UserError(_('Información faltante\n\nEl Banco %s no tiene un número BIC.') % (cmpl.destiny_bank_id.name))
                                cmpl_attrs.append(('BancoDestNal', cmpl.destiny_bank_id.sat_bank_id.bic))
                                if cmpl.destiny_bank_id.sat_bank_id.bic == '999':
                                    cmpl_attrs.append(('BancoDestExt', cmpl.destiny_frgn_bank))
                                transfers.append(('Transferencia', dict(cmpl_attrs)))
                            elif cmpl.type_key == 'payment':
                                cmpl_attrs.append(('MetPagoPol', cmpl.pay_method_id.code))
                                cmpl_attrs.append(('RFC', cmpl.rfc2.upper()))
                                payments.append(('OtrMetodoPago', dict(cmpl_attrs)))

                        if len(cfdis):
                            lnAttrs.append(cfdis[0])
                        if len(others):
                            lnAttrs.append(others[0])
                        if len(foreigns):
                            lnAttrs.append(foreigns[0])
                        if len(checks):
                            lnAttrs.append(checks[0])
                        if len(transfers):
                            lnAttrs.append(transfers[0])
                        if len(payments):
                            lnAttrs.append(payments[0])                        
                        lines.append(dict(lnAttrs))                        
                    mvAttrs.append(('Transaccion', lines))                    
                    mva = dict(mvAttrs)                    
                    mva['Transaccion'] = [ dict(i) for i in mva['Transaccion'] ]                   
                    entries.append(mva)                   
                if form.request_type in ('AF', 'FC'):
                    form.procedure_number = ""
                
                if form.request_type in ('DE', 'CO'):
                    form.order_number = ""
                polizas = {
                    "localizacion-mx": {
                        "login": {
                                "rfc":self.env['ir.config_parameter'].sudo().get_param('webservice.rfc_web'),
                                "clave":self.env['ir.config_parameter'].sudo().get_param('webservice.password')
                        },
                        "Polizas":
                    {
                        "Anio": str(period_id.date_start)[0:4],
                        "Certificado":"",
                        "Mes": str(period_id.date_start)[5:7],
                        "noCertificado":"",
                        "NumOrden": form.order_number,
                        "NumTramite": form.procedure_number,
                        "RFC": user.company_id.rfc,
                        "Sello":"",
                        "TipoSolicitud": form.request_type,
                        "Version":"1.1",
                        "Poliza": entries

                    },

                    
                            
                    }
                }
                
                headers = {'content-type': 'application/json'}        
                res = requests.post(str(url) + "/ce/polizas", data=json.dumps(polizas), headers=headers)
                respuesta = json.loads(res.content.decode("utf-8"))
                _logger.error("Resultado_polizas: %s", respuesta)
                ad = dict()
                if respuesta['Codigo'] == 1:
                    ad['archivo_generado'] = "Póliza"
                    ad['user_id'] = self.env.user.id
                    ad['año_fiscal'] = str(period_id.date_start)[0:4]
                    ad['periodo_declaracion'] = str(period_id.date_start)[5:7]
                    xml_recep = respuesta['Data']['Polizas']['xmlPolizas64']
                    result = self.env['declaraciones.sat'].create(ad)
                    xml_dec = base64.decodestring(str.encode(xml_recep))                           
                    xml_dec= xml_dec.decode("utf-8").replace('\r\n','')
                    

                    self.write({
                                'filename': filename,                            
                                'primary_file': xml_recep
                                })

                    attachment_obj = self.env['ir.attachment']   
              
                    data_at = {
                                'name': filename,
                                'datas': base64.encodestring(str.encode(xml_dec)),                        
                                #'datas_fname': filename,
                                'description': 'Archivo XML declaracion',
                                'res_model': 'declaraciones.sat',
                                'res_id': result.id,
                                'type': 'binary',                        
                    }
                    _logger.error('Adjunto: %s', data_at)
                    attach = attachment_obj.with_context({}).create(data_at)

                    xres = self.do_something_with_xml_attachment(attach)
                    
                else:
                  raise UserError(_("Error: %s" % respuesta['Descripcion']))

            else: # Auxiliar de Folios
                filename = self.env.user.company_id.rfc + str(form.year) + form.month + 'XF' + '.xml'
                days = calendar.monthrange(int(self.year),int(self.month))[1]                
                fecha_inicio = str(self.year) + '-' + str(self.month) + '-' + '01' + ' ' + '00:00:00'
                fecha_fin = str(self.year) + '-' + str(self.month) + '-' + str(days) + ' ' + '00:00:00'           
                folios = self.env['xmlcfdi'].search([('fecha_timbrado','>=', fecha_inicio),('fecha_timbrado','<=', fecha_fin)])                
                content = [('Version', '1.3'),
                         ('RFC', user.company_id.rfc),
                         ('Mes', period_id.date_start[5:7]),
                         ('Anio', period_id.date_start[0:4]),
                         ('TipoSolicitud', form.request_type),
                         ('unroot', entries)]
                if form.request_type in ('AF', 'FC'):
                    content.append(('NumOrden', form.order_number.upper()))
                    form.procedure_number = ""
                if form.request_type in ('DE', 'CO'):
                    content.append(('NumTramite', form.procedure_number))
                    form.order_number = ""
                data=[]
                for folio in folios:
                    data_lict = [('Fecha',folio.fecha_timbrado ),
                                  ('NumUnIdenPol',folio.name )
                                ]
                    fromcurrency = folio.currency_id.with_context(date=folio.fecha_timbrado)
                    comprobante = {                            
                                "UUID_CFDI": folio.cfdi_folio,
                                "Moneda": folio.currency_id.name,                  
                                "MetPagoAux": "",
                                "RFC": folio.rfc_receptor,
                                "MontoTotal": round(folio.total_docto,2),
                                "TipCamb": round(fromcurrency._get_conversion_rate(fromcurrency,self.env.user.company_id.currency_id),5)

                              }
                    data_lict.append(('ComprNal', [comprobante]))
                    data.append(dict(data_lict))
                    _logger.error("Datos a Enviar: %s", data)
                folios= { 
                       "localizacion-mx":
                       {
                       "login": 
                       {
                                "rfc":self.env['ir.config_parameter'].sudo().get_param('webservice.rfc_web'),
                                "clave":self.env['ir.config_parameter'].sudo().get_param('webservice.password')
                        },
                           
                              "RepAuxFol":
                             { 
                              "RepAuxFol":
                             { 
                              "Anio": str(period_id.date_start)[0:4], 
                              "Mes": str(period_id.date_start)[5:7], 
                              "NumOrden": form.order_number,
                              "NumTramite": form.procedure_number, 
                              "RFC": user.company_id.rfc, 
                              "TipoSolicitud": form.request_type,
                              "Version": 1.3,
                              "DetAuxFol": data
                                 
                                                              
                                  }
                                   } 
                                   }
                                   }
                                   
                
                headers = {'content-type': 'application/json'}        
                res = requests.post(str(url) + "/ce/auxfolios", data=json.dumps(folios), headers=headers)
                respuesta = json.loads(res.content.decode("utf-8"))
                _logger.error("Resultado_folios: %s", res)
                ad = dict()
                if respuesta['Codigo'] == 1:
                    ad['archivo_generado'] = "Auxiliar de Folios"
                    ad['user_id'] = self.env.user.id
                    ad['año_fiscal'] = period_id.date_start[0:4]
                    ad['periodo_declaracion'] = period_id.date_start[5:7]
                    xml_recep = respuesta['Data']['AuxFolios']['xmlAuxFolios64']
                    result = self.env['declaraciones.sat'].create(ad)
                    xml_dec = base64.decodestring(str.encode(xml_recep))                           
                    xml_dec= xml_dec.decode("utf-8").replace('\r\n','')
                    

                    self.write({
                                'filename': filename,                            
                                'primary_file': xml_recep
                                })

                    attachment_obj = self.env['ir.attachment']   
              
                    data_at = {
                                'name': filename,
                                'datas': base64.encodestring(str.encode(xml_dec)),                        
                                #'datas_fname': filename,
                                'description': 'Archivo XML declaracion',
                                'res_model': 'declaraciones.sat',
                                'res_id': result.id,
                                'type': 'binary',                        
                    }
                    _logger.error('Adjunto: %s', data_at)
                    attach = attachment_obj.with_context({}).create(data_at)

                    xres = self.do_something_with_xml_attachment(attach)
                    
                else:
                  raise UserError(_("Error: %s" % respuesta['Descripcion']))

        elif form.xml_target == 'helpers_account': 
            if form.request_type in ('AF', 'FC'):
                if len(form.order_number) != 13:
                    raise UserError(_('Número de orden erróneo\n\nVerifique que su número de orden contenga 13 caracteres (incluida la diagonal)'))
                if not re.compile('[A-Z]{3}[0-6][0-9][0-9]{5}(/)[0-9]{2}').match(form.order_number.upper()):
                    raise UserError(_('Número de orden erróneo\n\nVerifique que su número de orden tenga la siguiente estructura:\n  * Tres letras mayúsculas de la A al Z sin incluir la "Ñ"\n  * Un dígito entre 0 y 6\n  * Un dígito entre 0 y 9\n  * Cinco dígitos entre 0 y 9\n  * Una diagonal "/"\n  * Dos dígitos del entre 0 y 9'))
            if form.request_type in ('DE', 'CO'):
                if len(form.procedure_number) != 14:
                    raise UserError(_('Número de trámite erróneo\n\nVerifique que su número de trámite contenga 14 caracteres.')) 

            filename = self.env.user.company_id.rfc + str(form.year) + form.month + 'XC' + '.xml'
            if balance_ids is None:
                trialWizardObj = self.env['account.monthly_balance_wizard']                
                trial_balance_id = trialWizardObj.create({'chart_account_id': form.accounts_chart.id,
                                                         'company_id'       : user.company_id.id,
                                                         'period_id'        : period_id.id,
                                                         'partner_breakdown': False,
                                                         'output'           : 'list_view',})
                
                balance_ids = eval(trial_balance_id.get_info()['domain'][1:-1])[2]                
            balanceRecords = self.env['account.monthly_balance'].browse(balance_ids)            
            ctas = []
            ctasAttrs = []
            for record in balanceRecords:                
                    
                subctasAttrs = [('NumCta', record.account_code[0:100]),
                             ('DesCta', record.account_id.name[0:100]),
                             ('SaldoIni', round(record.initial_balance, 2)),                             
                             ('SaldoFin', round(record.ending_balance, 2))]                
                
                trialWizardObj_aux = self.env['account.account_lines_wizard']                    
                trial_auxiliar_id = trialWizardObj_aux.create({'account_id': record.account_id.id,
                                                         'company_id': user.company_id.id,
                                                         'period_id_start': period_id.id,
                                                         'period_id_stop': period_id.id,
                                                         'fical_year_id': form.year,
                                                         'partner_breakdown': False,
                                                         'output': 'list_view',})                
                
                auxiliar_ids = eval(trial_auxiliar_id.button_get_info()['domain'][1:-1])[2]
                _logger.error("Auxiliares: %s", auxiliar_ids)   
                auxiliarRecords = self.env['account.account_lines'].browse(auxiliar_ids) 
                
                auxAttrs = []
                subauxAttrs = []
                for auxiliar in auxiliarRecords:
                    
                    subauxAttrs = [('Concepto', auxiliar.name),
                                ('Debe', round(auxiliar.debit,2)),
                                 ('Fecha', auxiliar.move_date),
                                 ('NumUnIdenPol', auxiliar.move_name),                             
                                ('Haber', round(auxiliar.credit, 2))]
                    auxAttrs.append(dict(subauxAttrs))                
                subctasAttrs.append(('DetalleAux', auxAttrs))
                _logger.error('Subaux: %s', subctasAttrs)
                ctas.append(dict(subctasAttrs))
            content = [('Version', '1.3'),
                         ('RFC', user.company_id.rfc),
                         ('Mes', str(period_id.date_start)[5:7]),
                         ('Anio', str(period_id.date_start)[0:4]),
                         ('TipoSolicitud', form.request_type)]                         
            if form.request_type in ('AF', 'FC'):
                content.append(('NumOrden', form.order_number.upper()))
                form.procedure_number = ""
            if form.request_type in ('DE', 'CO'):
                content.append(('NumTramite', form.procedure_number))
                form.order_number = ""

            cuentas_subcuentas = { 
                 
                  "localizacion-mx":
                  { 
                    
                    "login": {
                                "rfc":self.env['ir.config_parameter'].sudo().get_param('webservice.rfc_web'),
                                "clave":self.env['ir.config_parameter'].sudo().get_param('webservice.password')
                              }, 
                    "AuxiliarCtas":
                    { 
                      "AuxiliarCtas":
                      { 
                        "Anio": str(period_id.date_start)[0:4], 
                        "Mes": str(period_id.date_start)[5:7], 
                        "NumOrden": form.order_number, 
                        "NumTramite": form.procedure_number, 
                        "RFC": user.company_id.rfc,  
                        "TipoSolicitud":form.request_type, 
                        "Version": 1.3, 
                        "Cuenta":ctas
                        
                              }
                               }
                                }
                                 }
            """dir = '/home'
            filename = "cuentas_suncuentas_2.json"
            with open(os.path.join(dir, filename), 'w') as file:
                json.dump(cuentas_subcuentas, file)"""  
            headers = {'content-type': 'application/json'}        
            res = requests.post(str(url) + "/ce/auxcuentas", data=json.dumps(cuentas_subcuentas), headers=headers)
            respuesta = json.loads(res.content.decode("utf-8"))
            _logger.error("Resultado_Cuentas: %s", res)
            ad = dict()
            if respuesta['Codigo'] == 1:
                ad['archivo_generado'] = "Auxiliar de Ceuntas y Sub-cuentas"
                ad['user_id'] = self.env.user.id
                ad['año_fiscal'] = str(period_id.date_start)[0:4]
                ad['periodo_declaracion'] = str(period_id.date_start)[5:7]
                xml_recep = respuesta['Data']['AuxCuentas']['xmlAuxAuentas64']
                result = self.env['declaraciones.sat'].create(ad)
                xml_dec = base64.decodestring(str.encode(xml_recep))                           
                xml_dec= xml_dec.decode("utf-8").replace('\r\n','')
                

                self.write({
                            'filename': filename,                            
                            'primary_file': xml_recep
                            })

                attachment_obj = self.env['ir.attachment']   
          
                data_at = {
                            'name': filename,
                            'datas': base64.encodestring(str.encode(xml_dec)),                        
                            #'datas_fname': filename,
                            'description': 'Archivo XML declaracion',
                            'res_model': 'declaraciones.sat',
                            'res_id': result.id,
                            'type': 'binary',                        
                }
                _logger.error('Adjunto: %s', data_at)
                attach = attachment_obj.with_context({}).create(data_at)

                xres = self.do_something_with_xml_attachment(attach)  

        return self._reopen_wizard(self.id)


    


    #@api.model                                                
    def do_zip(self):
        self.ensure_one()
        form = self
        (descriptor, zipname,) = tempfile.mkstemp('eaccount_', '__asti_')
        zipDoc = ZipFile(zipname, 'w')
        xmlContent = b64dec(form.stamped_file) if form.stamped_file else b64dec(form.primary_file)
        zipDoc.writestr(form.filename, xmlContent, zipfile.ZIP_DEFLATED)
        zipDoc.close()
        os.close(descriptor)
        filename = self.env.user.company_id.rfc + str(form.year) + form.month
        if form.xml_target == 'accounts_catalog':
            filename += 'CT'
        elif form.xml_target == 'trial_balance':
            filename += 'B' + form.trial_delivery
        elif form.xml_target == 'vouchers':
            filename += 'PL'
        elif form.xml_target == 'helpers':
            filename += 'XF'
        elif form.xml_target == 'helpers_account':
            filename += 'XC'
        filename += '.zip'
        self.write({ 'state': 'zip_done',
                     'zipped_file': b64enc(open(zipname, 'rb').read()),
                     'filename': filename})
        return self._reopen_wizard(self.id)



files_generator_wizard()


