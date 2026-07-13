# -*- encoding: utf-8 -*-

from odoo import api, fields, models, _, tools
from odoo.exceptions import UserError, ValidationError
import base64
from time import strftime
import datetime
import tempfile
import os
from dateutil.relativedelta import *
import requests
import json
import urllib
import logging
_logger = logging.getLogger(__name__)

class wizard_account_diot_mx(models.TransientModel):

    _name = 'account.diot.report'
   
    
    name        = fields.Char(string='Nombre de Archivo', readonly=True)
    company_id  = fields.Many2one('res.company', 'Compañia', required=True, default = lambda self: self.env.user.company_id)
    period_id   = fields.Many2one('account.period', 'Periodo',help='Select period', required=True,
                                 default=lambda self: self.env['account.period'].search([('date_start', '<=', fields.Date.today()), ('date_stop', '>=', fields.Date.today()), ('company_id', '=', self.env.user.company_id.id),('special','=',False)], limit=1))
    filename    = fields.Char(string='Archivo', size=128, readonly=True)    
    file        = fields.Binary(string='Archivo_txt', readonly=True, help='This file, you can import the SAT')
    
                                
    


    @api.model
    def do_something_with_xml_attachment(self, attach):

        return True

    #@api.model
    def create_diot(self):
        
        self.ensure_one() 
        
        webservice_url = self.env['ir.config_parameter'].sudo().get_param('webservice.url')
        if webservice_url == 'test':
            url = self.env['ir.config_parameter'].sudo().get_param('webservice.url_name_prue')
        if webservice_url == 'product':
            url = self.env['ir.config_parameter'].sudo().get_param('webservice.url_name_produc')
        filename = "%s-%s-%s.txt" % ("DIOT", self.company_id.name, strftime('%Y-%m-%d'))
        acc_tax_category_obj = self.env['account.tax.category']       
        period = self.period_id
        partner_company_id = self.company_id.partner_id.id
        category_iva_ids = acc_tax_category_obj.search([('name', 'in', ('IVA', 'IVA-EXENTO', 'IVA-TASA CERO', 'IVA-RET', 'IVA-PART'))])        
        period_ids = self.env['account.period'].search([('name','=',period.name)])
        pre_diot_obj = self.env['account.invoice.diot']   
        
        lines_prediot = pre_diot_obj.search([('periodo_reportado','=',period.name)])
        
        partner_diot = []
        partner_diot_line = {}
        for line in lines_prediot: 
            partner_id = line.name.partner_id            
            partner_vat = (partner_id.rfc or '').replace('-', '').replace('_', '').replace(' ', '').upper()            
            partner_tin = partner_id.nif_diot and partner_id.nif_diot.upper() or False
            if partner_id.tipo_tercero ==  '04':
                partner_id.paises_diot = ""
                partner_id.nacionalidad = ""
                partner_tin = ""
                #partner_id.name = ""            
            if partner_id.tipo_tercero == '15':
                partner_id.paises_diot = ""
                partner_id.nacionalidad = ""
                partner_tin = ""
                partner_id.name = ""
                partner_vat = ""            
            partner_diot_line = {
                    "tipo_tercero": partner_id.tipo_tercero,
                    "tipo_operacion": partner_id.tipo_operacion,
                    "rfc": partner_vat,
                    "numero_id_fiscal": partner_tin, 
                    "nombre_del_extranjero": partner_id.name, 
                    "pais_de_residencia": partner_id.paises_diot or "", 
                    "nacionalidad": partner_id.nacionalidad,
                    "actos_pagados_15_16_iva": 0,
                    'actos_pagados_15_iva':0, 
                    "iva_pagado_no_acreditable_15_16":0, 
                    "actos_pagados_10_11_iva":0, 
                    "actos_pagados_10_iva":0, 
                    "actos_pagados_con_estimulo_fronterizo":0, 
                    "iva_pagado_no_acreditable_10_11": 0, 
                    "iva_pagado_no_acreditable_region_fronteriza": 0, 
                    "actos_pagados_por_importacion_bienes_servicios_15_16": 0, 
                    "iva_pagado_no_acreditable_por_importacion_15_16": 0, 
                    "actos_pagados_por_importacion_bienes_servicios_10_11": 0, 
                    "iva_pagado_no_acreditable_por_importacion_10_11": 0,
                    "actos_pagados_por_importacion_exentos": 0,
                    "actos_pagados_tasa_cero":0,
                    "actos_pagados_exentos":0,
                    "iva_retenido":0, 
                    "iva_devoluciones_descuentos_sobre_compras":0, 
                    "total_operaciones":0, 
                    "total_actos_pagados_15_16_iva":0, 
                    "total_actos_pagados_15_iva":0, 
                    "total_iva_pagado_no_acreditable_15_16":0, 
                    "total_pagados_10_11_iva":0, 
                    "total_pagados_10_iva":0, 
                    "total_pagados_con_estimulo_fronterizo":0, 
                    "total_iva_pagado_no_acreditable_10_11":0, 
                    "total_pagado_no_acreditable_region_fronteriza":0, 
                    "total_actos_pagados_por_importacion_bienes_servicios_15_16":0, 
                    "total_iva_pagado_no_acreditable_por_importacion_15_16":0, 
                    "total_actos_pagados_por_importacion_bienes_servicios_10_11":0, 
                    "total_iva_pagado_no_acreditable_por_importacion_10_11":0, 
                    "total_actos_pagados_por_importacion_exentos":0, 
                    "total_actos_pagados_tasa_cero":0, 
                    "total_actos_pagados_exentos":0, 
                    "total_iva_retenido":0, 
                    "total_iva_devoluciones_descuentos_sobre_compras":0, 
                    "total_iva_pagado_po_importaciones_bienes_servicios":0
                    } 
            if line.tasa_tax == '16.0' or line.tasa_tax == '15':
                partner_diot_line ['actos_pagados_15_16_iva'] = int(line.monto_base)
                partner_diot_line['iva_pagado_no_acreditable_15_16'] = int(line.monto_impuesto)
                partner_diot_line['total_actos_pagados_15_16_iva'] = int(line.monto_base)
                partner_diot_line['total_iva_pagado_no_acreditable_15_16'] = int(line.monto_impuesto)
            if line.tasa_tax == '10.0' or line.tasa_tax == '11':
                partner_diot_line ['actos_pagados_10_11_iva'] = int(line.monto_base)
                partner_diot_line['iva_pagado_no_acreditable_10_11'] = int(line.monto_impuesto)
                partner_diot_line['total_pagados_10_11_iva'] = int(line.monto_base)
                partner_diot_line['total_iva_pagado_no_acreditable_10_11'] = int(line.monto_impuesto)
            if line.categoria_impuesto == 'IVA-TASA CERO':
                partner_diot_line ['actos_pagados_tasa_cero'] = int(line.monto_base)
                partner_diot_line['total_actos_pagados_tasa_cero'] = int(line.monto_base)
            if line.categoria_impuesto == 'IVA-RET':
                partner_diot_line ['iva_retenido'] = int(line.monto_base)
                partner_diot_line['total_iva_retenido'] = int(line.monto_base)
            if line.categoria_impuesto == 'IVA-EXENTO':
                partner_diot_line ['actos_pagados_exentos'] = int(line.monto_base)
                partner_diot_line['total_actos_pagados_exentos'] = int(line.monto_base)
            if line.tasa_tax == '8.0':
                partner_diot_line ['actos_pagados_con_estimulo_fronterizo'] = int(line.monto_base)
                partner_diot_line['total_pagado_no_acreditable_region_fronteriza'] = int(line.monto_base)
                partner_diot_line['total_pagado_no_acreditable_region_fronteriza'] = int(line.monto_impuesto)
                partner_diot_line['iva_pagado_no_acreditable_region_fronteriza'] = int(line.monto_impuesto)
            
            partner_diot.append(partner_diot_line)   
        
        report_diot = {
                    "localizacion-mx":
                    { 
                    "login":
                    { 
                        "rfc":self.env['ir.config_parameter'].sudo().get_param('webservice.rfc_web'),
                          "clave":self.env['ir.config_parameter'].sudo().get_param('webservice.password')
                     },
                     "diot": partner_diot
                      
                    } 
                }

        dir = '/home'
        filename_file = "repordiot.json"
        with open(os.path.join(dir, filename_file), 'w') as file:
            json.dump(report_diot, file)
        _logger.error('Datos: %s', report_diot)
        headers = {'content-type': 'application/json'}        
        res = requests.post(str(url) + "/ce/diot", data=json.dumps(report_diot), headers=headers)
        respuesta = json.loads(res.content.decode("utf-8"))
            
        ad = dict()
        if respuesta['Codigo'] == 1:
            ad['archivo_generado'] = "Reporte DIOT"
            ad['user_id'] = self.env.user.id
            ad['año_fiscal'] = period_ids.fiscalyear_id.name
            ad['periodo_declaracion'] = period_ids.name
            txt_recep = respuesta['Data']['Diot']['txtDiot64']
            result = self.env['declaraciones.sat'].create(ad)
            txt_dec = base64.decodestring(str.encode(txt_recep))                           
            txt_dec= txt_dec.decode("utf-8").replace('\r\n','')
            

            self.write({
                        'filename': filename,                            
                        'file': txt_recep
                        })
            for lines in lines_prediot:
                lines.state = 'done'
                #lines.name.partner_id.name = lines.proveedor
            attachment_obj = self.env['ir.attachment']   
      
            data_at = {
                        'name': filename,
                        'datas': base64.encodestring(str.encode(txt_dec)),                        
                        #'datas_fname': filename,
                        'description': 'Archivo Txt de DIOT',
                        'res_model': 'declaraciones.sat',
                        'res_id': result.id,
                        'type': 'binary',                        
            }
            _logger.error('Adjunto: %s', data_at)
            attach = attachment_obj.with_context({}).create(data_at)

            xres = self.do_something_with_xml_attachment(attach)

        

        return {'type'      : 'ir.actions.act_window',
                'view_type' : 'form',
                'view_mode' : 'form',
                'res_id'    : self.id,
                'views'     : [(False, 'form')],
                'res_model' : 'account.diot.report',
                'target'    : 'new',
                }
        