from odoo import api, fields, models, _, tools
from datetime import datetime
import time
from odoo import SUPERUSER_ID
import time
import dateutil
import dateutil.parser
from datetime import datetime, date
from odoo.exceptions import UserError, RedirectWarning, ValidationError
import re
import requests
import json
import urllib
import traceback
import qrcode
import codecs
import os
import sys
import io
from pytz import timezone
import pytz
import base64
from odoo.tools import DEFAULT_SERVER_DATETIME_FORMAT, DEFAULT_SERVER_DATE_FORMAT
import logging
_logger = logging.getLogger(__name__)
from . import amount_to_text_es_MX


class AccountInvoice(models.Model):    
    _inherit ='account.move'


    TipoDeComprobante = fields.Many2one('sat.tipo.comprobante', 'Tipo de Comprobante', required=False, copy=False)

    
    @api.model
    def _get_invoice(self):
        if self.move_type in ('in_invoice','in_refund'):
            self.name_invoice = '.'
            return

        fname = ""
        if not self.compañia_emisora_id.partner_id.rfc and not self.compañia_emisora_id.partner_id.rfc :
            raise UserError(_("Error!\nLa Compañía Emisora no tiene definido el RFC."))
        fname += (self.compañia_emisora_id.partner_id.rfc or self.compañia_emisora_id.partner_id.rfc) + '_' + (self.name or '')
        
        self.name_invoice = fname
    

    #@api.model
    @api.depends('amount_total','currency_id')
    def _get_amount_to_text(self):
        for record in self:
          record.amount_to_text = amount_to_text_es_MX.get_amount_to_text(self, record.amount_total, record.currency_id.name)

    

    @api.model
    def create(self, vals_list):
        res = super(AccountInvoice, self).create(vals_list)
        sat_tipo_obj = self.env['sat.tipo.comprobante']       
        _logger.error('sat: %s', sat_tipo_obj)
        type_document = res.move_type
        if type_document == 'out_invoice':
            tipo_id = sat_tipo_obj.search([('code','=','I')], limit=1)
            res.TipoDeComprobante = tipo_id[0].id if tipo_id else False
        elif type_document == 'out_refund':
            tipo_id = sat_tipo_obj.search([('code','=','E')], limit=1)
            res.TipoDeComprobante = tipo_id[0].id if tipo_id else False


        return res     
        
    @api.model
    def do_something_with_xml_attachment(self, attach):

        return True

    def Timbrar_factura(self):
        login = {}
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
            "rfc": self.company_id.rfc_web_1,
            "clave": self.company_id.password_1
            }
        if webservice_url == 'test':
            url = self.env['ir.config_parameter'].sudo().get_param('webservice.url_name_prue')
        if webservice_url == 'product':
            url = self.env['ir.config_parameter'].sudo().get_param('webservice.url_name_produc')
    
       

        fname_invoice = self.name_invoice and self.name_invoice + \
                            '.xml' or ''

       
        date_ctx = {'date': self.date_invoice_tz and time.strftime(
            '%Y-%m-%d', time.strptime(self.date_invoice_tz,
            '%Y-%m-%d %H:%M:%S')) or False}
        currency = self.currency_id
        rate = self.currency_id.with_context(date_ctx).rate
        rate = rate != 0 and 1.0/rate or 0.0
        if currency.name == 'MXN':
            rate = 1
        else:
            rate = '%.4f' % rate or 1       
        self.write({'TipoCambio': rate})
        lineas_facturas = []
        account_tax_obj = self.env['account.tax']
        total_impuestos_trasladados = 0.0
        total_impuestos_retenidos = 0.0
        totallines = 0.0
        #totallines = 0.0
        amount_subtotal = 0.0
        totaldescuento = 0.0
       
        for line in self.invoice_line_ids:
            
            sat_product_id = line.product_id.sat_product_id
            if not sat_product_id:
                sat_product_id = line.product_id.categ_id.sat_product_id
            if not sat_product_id:
                raise UserError(_("Error!\nEl producto: %s No cuenta con la Clave de Producto/Servicio del SAT." % line.product_id.name))
            sat_uom_id = line.product_uom_id.sat_uom_id
            if not sat_uom_id:
                raise UserError(_("Error!\nLa Unidad de Medida: %s No cuenta con la Clave SAT." % line.product_uom_id.name))
            
            codigo_producto = ""
            if line.product_id.no_identity_type:
                if line.product_id.no_identity_type != 'none':
                    if line.product_id.no_identity_type == 'default_code':
                         codigo_producto = line.product_id.default_code 
                    elif line.product_id.no_identity_type == 'barcode':
                        codigo_producto = line.product_id.barcode
                    else:
                        codigo_producto = line.product_id.no_identity_other
            producto = line.name #.replace('&','amp;').replace('<','lt;').replace('>','gt;').replace('"','quot;')
            #_logger.error("Producto: %s", producto)
            producto = str(producto).encode("utf-8")
            base64_dato = base64.b64encode(producto)
            producto_dec = base64_dato.decode("utf-8")
            price_unit = line.price_unit * (1 - (line.discount or 0.0) / 100.0) 
            descuento = line.price_unit * (line.discount or 0.0) / 100.0
            price_subtotal = line.price_unit * line.quantity
            if self.partner_id.rfc != "XAXX010101000":
                if line.discount == 0:            
                    line_dict = {
                              'Cantidad': line.quantity,
                              "ObjetoImp": line.objimp_id.c_ObjetoImp,
                              'ClaveProdServ': sat_product_id.code,
                              'ClaveUnidad': sat_uom_id.code,
                              'Unidad': sat_uom_id.name,
                              'Descripcion': producto_dec or '',
                              'ValorUnitario': "%.2f" % (price_unit or 0.0),
                              'Importe': "%.2f" % (line.price_subtotal or 0.0),
                              'Descuento': "",
                              'NoIdentificacion': codigo_producto,         
                              "CuentaPredial": {
                                              'Numero': ""
                                            },
                              }
                    #totaldescuentos = ""
                    _logger.error("line_dict: %s", line_dict)
                else:
                    line_dict = {
                              'Cantidad': line.quantity,
                              "ObjetoImp": line.objimp_id.c_ObjetoImp,
                              'ClaveProdServ': sat_product_id.code,
                              'ClaveUnidad': sat_uom_id.code,
                              'Unidad': sat_uom_id.name,
                              'Descripcion': producto_dec or '',
                              'ValorUnitario': "%.2f" % (line.price_unit or 0.0),
                              'Importe': "%.2f" % (price_subtotal or 0.0),
                              'Descuento': "%.2f" % ((line.quantity * descuento) or 0.0),
                              'NoIdentificacion': codigo_producto,         
                              "CuentaPredial": {
                                              'Numero': ""
                                            },
                              }
            else:
                if line.discount == 0:            
                    line_dict = {
                              'Cantidad': line.quantity,
                              "ObjetoImp": line.objimp_id.c_ObjetoImp,
                              'ClaveProdServ': sat_product_id.code,
                              'ClaveUnidad': sat_uom_id.code,
                              'Unidad': sat_uom_id.name,
                              'Descripcion': producto_dec or '',
                              'ValorUnitario': "%.2f" % (price_unit or 0.0),
                              'Importe': "%.2f" % (line.price_subtotal or 0.0),
                              'Descuento': "",
                              'NoIdentificacion': line.no_ticket,         
                              "CuentaPredial": {
                                              'Numero': ""
                                            },
                              }
                    #totaldescuentos = ""
                    _logger.error("line_dict: %s", line_dict)
                else:
                    line_dict = {
                              'Cantidad': line.quantity,
                              "ObjetoImp": line.objimp_id.c_ObjetoImp,
                              'ClaveProdServ': sat_product_id.code,
                              'ClaveUnidad': sat_uom_id.code,
                              'Unidad': sat_uom_id.name,
                              'Descripcion': producto_dec or '',
                              'ValorUnitario': "%.2f" % (line.price_unit or 0.0),
                              'Importe': "%.2f" % (price_subtotal or 0.0),
                              'Descuento': "%.2f" % ((line.quantity * descuento) or 0.0),
                              'NoIdentificacion': "510",         
                              "CuentaPredial": {
                                              'Numero': ""
                                            },
                              }

            totallines += round((line.quantity * descuento), 2)
            
            if line.discount > 0:
                
                totalsubtotal = line.price_unit * line.quantity
                amount_subtotal += totalsubtotal
                totaldescuentos = totalsubtotal * ((line.discount or 0.0) / 100.0)                  
                totaldescuento = round(totallines, 2)
            else:
                amount_subtotal += line.price_subtotal


                _logger.error("TotalBueno: %s", totaldescuento)
            
            taxes_line = line.tax_ids.compute_all(price_unit, self.currency_id, line.quantity, line.product_id, self.partner_id)['taxes']

            _logger.error('Impuestos1: %s', taxes_line) 

            line_dict_impuestos_t = []
            line_dict_impuestos_r = []
            totalredondeo = 0.0
            if line.objimp_id.c_ObjetoImp == '02':
               
                if taxes_line:  
                    for tax in taxes_line:
                        tax_id = tax['id']
                        tax_name = tax['name']
                        tax_amount = tax['amount']   
                        _logger.error('tax_amount: %s', tax_amount)                                        
                        tax_br = account_tax_obj.browse(tax_id)
                        sat_tipo_factor = tax_br.sat_tipo_factor_id.name
                        sat_code_tax = tax_br.sat_code_tax.code                                       
                        base_tax = tax['base']                    
                        sat_tasa_cuota = abs(tax_br.amount)                    
                        if not tax_br.sat_tasa_cuota:
                            raise UserError(_("Error no cuentas con el valor Tasa/Custo del Impuesto:%s" % tax_name))
                        if not tax_br.sat_code_tax:
                            raise UserError(_("Error no cuentas con el valor Clave de Impuesto SAT del Impuesto:%s" % tax_name))
                        if sat_tasa_cuota > 1.1:
                            sat_tasa_cuota = sat_tasa_cuota/100.0
                        if tax_amount < 0:
                            #tax_amount = round(tax_amount, 6)
                            total_impuestos_retenidos += abs(tax_amount)
                            line_dict_impuestos_r.append( {
                                                  
                                                  
                                                  "Retencion": {
                                                  "Base": "%.2f" % (base_tax),
                                                  "Importe": "%.2f" % (abs(tax_amount)),
                                                  "Impuesto": sat_code_tax,
                                                  "TasaOCuota": "%.6f" % (sat_tasa_cuota),
                                                  "TipoFactor": sat_tipo_factor
                                                   }
                                                  }
                                                                                              
                                              )
                            #_logger.error('line_dict_impuestos_r: %s', line_dict_impuestos_r)
                        else:
                            if sat_tipo_factor != "Exento":  
                                #total_impuestos_trasladados = '%.6f' % (tax_amount)
                                total_impuestos_trasladados += abs(total_impuestos_trasladados)
                                line_dict_impuestos_t.append( {  
                                                      
                                                 
                                                    "Traslado": {
                                                      "Base": "%.2f" % (base_tax),
                                                      "Importe": "%.2f" % (tax_amount),
                                                      "Impuesto": sat_code_tax,
                                                      "TasaOCuota": "%.6f" % (sat_tasa_cuota),
                                                      "TipoFactor": sat_tipo_factor
                                                    }
                                                  }

                                                )
                                
                            else:
                                line_dict_impuestos_t.append( {  
                                                      
                                                  
                                                    "Traslado": {
                                                      "Base": "%.2f" % (base_tax),                                                  
                                                      "Impuesto": sat_code_tax,                                                  
                                                      "TipoFactor": sat_tipo_factor
                                                    }
                                                  }
                                                 
                                              )
                    line_dict['InformacionAduanera'] = {
                                          "NumeroPedimento": ""
                                        }

                    line_dict['Parte'] = {
                                            "Parte":
                                            {
                                               "Concepto":
                                                 [
                                                    
                                                 ]
                                            }
                                        }
                    
                    line_dict['Impuestos']= {'Traslados': line_dict_impuestos_t,
                                              'Retenciones': line_dict_impuestos_r}   
                    lineas_facturas.append(line_dict)
                    
                else:

                    line_dict['Impuestos'] = {}                

                    line_dict['InformacionAduanera'] = {
                                              "NumeroPedimento": ""
                                            }
        
                    line_dict['Parte'] = {
                                                "Parte":
                                                {
                                                   "Concepto":
                                                     [
                                                        
                                                     ]
                                                }
                                            }
                    lineas_facturas.append(line_dict)
            else:
                line_dict['Impuestos'] = {}                

                line_dict['InformacionAduanera'] = {
                                          "NumeroPedimento": ""
                                        }
    
                line_dict['Parte'] = {
                                            "Parte":
                                            {
                                               "Concepto":
                                                 [
                                                    
                                                 ]
                                            }
                                        }
                lineas_facturas.append(line_dict)
                
        tipos_impuestos = {}
        totalimpretenidos = 0
        totalimptrasladados = 0  
        traslado = []      
        retension = []
        if line.objimp_id.c_ObjetoImp == '02':
            if self.tax_line_ids:
                #_logger.error('line_tax: %s', self.tax_line_ids)
                for line_tax in self.tax_line_ids:
                    _logger.error('line_tax: %s', line_tax.tax_id)
                    sat_tipo_factor = line_tax.tax_id.sat_tipo_factor_id.name
                    sat_code_tax = line_tax.tax_id.sat_code_tax.code
                    sat_tasa_cuota = line_tax.tax_id.amount
                    line_tax_id_amount = abs(line_tax.amount or 0.0) 
                    if abs(sat_tasa_cuota) > 1:
                        sat_tasa_cuota = abs(sat_tasa_cuota)/100.0           
                    if line_tax.amount < 0:
                        totalimpretenidos += line_tax_id_amount      
                        retension.append(
                          {
                            "Retencion": 
                              {
                                   "Impuesto": sat_code_tax,
                                   "Importe": "%.2f" % (line_tax_id_amount),                 
                              }
                         }
                       )
                    else:
                        if sat_tipo_factor != "Exento":
                            totalimptrasladados += line_tax_id_amount
                            traslado.append(
                              {
                                    "Traslado": 
                                    {
                                      "Base": "%.2f" % (line.price_subtotal),
                                      "Impuesto": sat_code_tax,
                                      "TipoFactor": sat_tipo_factor,
                                      "TasaOCuota": "%.6f" % (sat_tasa_cuota),
                                      "Importe": "%.2f" % (line_tax_id_amount),                          
                                    }
                              }
                            )
                        else:
                            traslado.append(
                              {
                                    "Traslado": 
                                    {
                                      
                                                                
                                    }
                              }
                    
                            )
                tipos_impuestos['Retenciones'] = retension
                tipos_impuestos['Traslados'] = traslado
                tipos_impuestos['TotalImpuestosRetenidos'] = "%.2f" % (totalimpretenidos)
                tipos_impuestos['TotalImpuestosTrasladados'] = "%.2f" % (totalimptrasladados)           
            else:
                
                tipos_impuestos={}
        else:
            tipos_impuestos={}

        
         
        Cfdi_Relacionados = [] 
        InformacionGlobal = {}
        Cfdi_Relacionados_1 =[]  
       
        if self.type_rel_cfdi_ids:
            if not self.type_rel_id:
                raise UserError("Error !\nDebes identificar el Tipo de Relacion para los CFDI.")            
            for cfdi_rel in self.type_rel_cfdi_ids:
                 Cfdi_Relacionados_1.append({'UUID': cfdi_rel.invoice_id.UUID})
                 
                 #_logger.error("UUID: %s", Cfdi_Relacionados_1)
            Cfdi_Relacionados.append({                                               
                                  "CfdiRelacionado": Cfdi_Relacionados_1,                                                   
                                                                                        
                                  "TipoRelacion": self.type_rel_id.code,
                                                      
                                   })
        

                
       
        if self.partner_id.rfc == "XAXX010101000":                                  
            InformacionGlobal = {
                        "Periodicidad": self.periodicidad.c_Periodicidad,
                        "Meses": self.meses_id.c_Meses,
                        "Año": self.year_report,
                    }
            codigopostalreceptor = self.direccion_compañia_id.sat_codigopostal_id.code
            CondicionesDePago = ''
            
        else:
            InformacionGlobal = {}  
            codigopostalreceptor = self.partner_id.sat_codigopostal_id.code 
            CondicionesDePago = self.invoice_payment_term_id.name if self.invoice_payment_term_id else ''
             

        if not self.direccion_compañia_id.regimen_fiscal_id:
            raise UserError("Error!\nLa Compañía no tiene definido un Regimen Fiscal, por lo cual no puede emitir el Recibo CFDI.")
        if not self.direccion_compañia_id.rfc:
            raise UserError("Error!\nLa Compañía no tiene definido un RFC, por lo cual no puede emitir el Recibo CFDI.")
        if not self.direccion_compañia_id.sat_codigopostal_id:
            raise UserError("Error!\nLa Compañía no tiene definido un Código Postal, por lo cual no puede emitir el Recibo CFDI.")
        if not self.compañia_emisora_id.codigopostal_sat_id:
            raise UserError("Error!\nLa Compañía no tiene definido un Código Postal, por lo cual no puede emitir el Recibo CFDI.")
        if not self.partner_id.rfc:
            raise UserError("Error!\nel Cliente no tiene definido un RFC, Favor de validar")
        if self.UUID != False:
             raise UserError("Error!\nEsta factura ya cuenta con UUID. Favor de generar una nueva")
        if self.currency_id.sat_currency_id == "":
             raise UserError("Error!\nLa Moneda no esta Configurada con su código SAT")
        if self.direccion_compañia_id.sat_codigopostal_id.code == '00000':
             raise UserError("Error!\nEl Código Postal no en valido para Timbrado") 
        #if not (self.compañia_emisora_id.date_start <= self.invoice_date and self.compañia_emisora_id.date_end >= self.invoice_date):
        #    raise UserError(_("Error !!!\nLa fecha de la factura está fuera del rango de Vigencia del Certificado, por favor revise."))
        if self.direccion_compañia_id.company_type == 'person':
            raise UserError(_("La Empresa - (ID: %s) %s - no está definida como Compañía o Persona Fisica, para usarlo en Facturas, es necesario que la defina como Compañía...")) 
        

            
        rfc_cliente = self.direccion_compañia_id.rfc
        rfc_clie = str(rfc_cliente).encode("utf-8")
        base64_rfc = base64.b64encode(rfc_clie)
        rfc_dec = base64_rfc.decode("utf-8")

        rfc_proveedor = self.partner_id.rfc.upper()
        rfc_prove = str(rfc_proveedor).encode("utf-8")
        base64_rfc_prov = base64.b64encode(rfc_prove)
        rfc_dec_prov = base64_rfc_prov.decode("utf-8")

        name_emisor = self.compañia_emisora_id.name
        name_emi = str(name_emisor).encode("utf-8")
        base64_name_clie = base64.b64encode(name_emi)
        name_emi_dec = base64_name_clie.decode("utf-8")

        name_receptor = self.partner_id.name
        name_rec = str(name_receptor).encode("utf-8")
        base64_name_recp = base64.b64encode(name_rec)
        name_rec_dec = base64_name_recp.decode("utf-8")

        self_tz = self.with_context(tz=self.env.user.partner_id.tz)        
        self.invoice_datetime = fields.datetime.now()        
        date = fields.Datetime.context_timestamp(self_tz, fields.Datetime.from_string(self.invoice_datetime))       
        
        date_invoice = fields.Datetime.from_string(str(self.invoice_date) + ' ' +str(date)[11:19])
       
        total1=0.0
        total2=0.0
        total = "%.2f" % (float("%.2f" % (amount_subtotal)) - float("%.2f" % (totalimpretenidos)) + float("%.2f" % (totalimptrasladados)) - float("%.2f" % (totaldescuento)))
        if self.type_rel_cfdi_ids:
            timbre_factura = {
                            "localizacion-mx": {
                                "Documento": {
                                    "Comprobante": {
                                        "Adenda": "",
                                        "Certificado": "",
                                        "CfdiRelacionados": Cfdi_Relacionados,
                                        "Complemento": {
                                            "Pagos": {
                                                "Pago": [],
                                                "Version": ""
                                            },
                                            "TimbreFiscaldigital": {
                                                "FechaTimbrado": "",
                                                "NoCertificadoSAT": "",
                                                "RfcProvCertif": "",
                                                "SelloCFD": "",
                                                "SelloSAT": "",
                                                "TimbreFiscaldigital": "",
                                                "UUID": "",
                                                "Version": ""
                                            }
                                        },
                                        "Conceptos": {
                                            "Concepto": lineas_facturas
                                        },
                                        "InformacionGlobal": InformacionGlobal,
                                        "CondicionesDePago": CondicionesDePago,
                                        "FacAtrAdquirente" : "",
                                        "Confirmacion": "",
                                        "Descuento": "%.2f" % (totaldescuento or 0.0),
                                        "Emisor": {
                                            "Nombre": name_emi_dec,
                                            "RegimenFiscal": self.direccion_compañia_id.regimen_fiscal_id.code,
                                            "Rfc": rfc_dec
                                        },
                                        "Fecha": date_invoice and time.strftime('%Y-%m-%dT%H:%M:%S', time.strptime(str(date_invoice), '%Y-%m-%d %H:%M:%S')),
                                        "Folio": self.name,
                                        "FormaPago": self.FormaPago.code,
                                        "Exportacion": self.exportacion_id.c_Exportacion,
                                        "Impuestos":tipos_impuestos,
                                        "LugarExpedicion": self.direccion_compañia_id.sat_codigopostal_id.code,
                                        "MetodoPago": str(self.MetodoPago.code),
                                        "Moneda": self.currency_id.sat_currency_id.code,
                                        "NoCertificado": "",
                                        "Receptor": {
                                            "Nombre": name_rec_dec,
                                            "NumRegIdTrib": "",
                                            "RFc": rfc_dec_prov,                    
                                            "UsoCFDI": self.UsoCFDI.code,
                                            "RegimenFiscalReceptor": self.partner_id.regimen_fiscal_id.code,                    
                                            "DomicilioFiscalReceptor": codigopostalreceptor
                                        },
                                        "Sello": "",
                                        "Serie": self.journal_id.code,#self.journal_id.sequence_id.prefix and self.journal_id.sequence_id.prefix.replace('/','').replace(' ','').replace('-','') or '',
                                        "Subtotal":  "%.2f" % (amount_subtotal or 0.0),
                                        "TipoCambio": rate,
                                        "TipoDeComprobante": self.TipoDeComprobante.code,
                                        "Total": total,#float("%.2f" % (amount_subtotal)) - float("%.2f" % (totalimpretenidos)) + float("%.2f" % (totalimptrasladados)) - float("%.2f" % (totaldescuento)),
                                        "Version": "4.0"
                                    },
                                    "Operacion": "TIMBRAR",
                                    "TipoDocumento": "FACTURA"
                                },
                                "login": login,
                            }
                        }

        else:
            timbre_factura = {
                            "localizacion-mx": {
                                "Documento": {
                                    "Comprobante": {
                                        "Adenda": "",
                                        "Certificado": "",
                                        "CfdiRelacionados": [
                                                         {
                                                        "CfdiRelacionado": [],
                                                        "TipoRelacion": ""
                                                    }
                                        ],
                                        "Complemento": {
                                            "Pagos": {
                                                "Pago": [],
                                                "Version": ""
                                            },
                                            "TimbreFiscaldigital": {
                                                "FechaTimbrado": "",
                                                "NoCertificadoSAT": "",
                                                "RfcProvCertif": "",
                                                "SelloCFD": "",
                                                "SelloSAT": "",
                                                "TimbreFiscaldigital": "",
                                                "UUID": "",
                                                "Version": ""
                                            }
                                        },
                                        "Conceptos": {
                                            "Concepto": lineas_facturas
                                        },
                                        "InformacionGlobal": InformacionGlobal,
                                        "CondicionesDePago": CondicionesDePago,
                                        "FacAtrAdquirente" : "",
                                        "Confirmacion": "",
                                        "Descuento": "%.2f" % (totaldescuento or 0.0),
                                        "Emisor": {
                                            "Nombre": name_emi_dec,
                                            "RegimenFiscal": self.direccion_compañia_id.regimen_fiscal_id.code,
                                            "Rfc": rfc_dec
                                        },
                                        "Fecha": date_invoice and time.strftime('%Y-%m-%dT%H:%M:%S', time.strptime(str(date_invoice), '%Y-%m-%d %H:%M:%S')),
                                        "Folio": self.name,
                                        "FormaPago": self.FormaPago.code,
                                        "Exportacion": self.exportacion_id.c_Exportacion,
                                        "Impuestos":tipos_impuestos,
                                        "LugarExpedicion": self.direccion_compañia_id.sat_codigopostal_id.code,
                                        "MetodoPago": str(self.MetodoPago.code),
                                        "Moneda": self.currency_id.sat_currency_id.code,
                                        "NoCertificado": "",
                                        "Receptor": {
                                            "Nombre": name_rec_dec,
                                            "NumRegIdTrib": "",
                                            "RFc": rfc_dec_prov,                    
                                            "UsoCFDI": self.UsoCFDI.code,
                                            "RegimenFiscalReceptor": self.partner_id.regimen_fiscal_id.code,                    
                                            "DomicilioFiscalReceptor": codigopostalreceptor
                                        },
                                        "Sello": "",
                                        "Serie": self.journal_id.code,#self.journal_id.sequence_id.prefix and self.journal_id.sequence_id.prefix.replace('/','').replace(' ','').replace('-','') or '',
                                        "Subtotal":  "%.2f" % (amount_subtotal or 0.0),
                                        "TipoCambio": rate,
                                        "TipoDeComprobante": self.TipoDeComprobante.code,
                                        "Total": total,#float("%.2f" % (amount_subtotal)) - float("%.2f" % (totalimpretenidos)) + float("%.2f" % (totalimptrasladados)) - float("%.2f" % (totaldescuento)),
                                        "Version": "4.0"
                                    },
                                    "Operacion": "TIMBRAR",
                                    "TipoDocumento": "FACTURA"
                                },
                                "login": login,
                            }
                        }

        datos_cod = str(timbre_factura).encode('utf-8')
        base64_datos = base64.b64encode(datos_cod)
        cadena = ""
        cadena = base64_datos.decode("utf-8")
        cadena_data = cadena
        data = {

               "datos":cadena_data
                

               }

        """dir = '/home'
        filename = "facturaegresos40.json"
        with open(os.path.join(dir, filename), 'w') as file:
            json.dump(timbre_factura, file)"""
        _logger.error('datos_timbre: %s', timbre_factura)
        _logger.error('data: %s', data)
        
        headers = {'content-type': 'application/json'}        
        res = requests.post(str(url) + "/Timbrar/CFDI", data=json.dumps(data), headers=headers)
        respuesta = json.loads(res.content.decode("utf-8"))
        _logger.error('respuesta: %s', respuesta)
       
        xml_recep = ""
        ad = dict()
        cfdi = dict()
        if respuesta['Codigo'] == 1:
            _logger.error('sello: %s', respuesta['Data']['Timbre']['SelloEmisor'])
            ad['UUID'] = respuesta['Data']['Timbre']['FolioFsical']
            ad['FechaTimbrado'] = self.invoice_datetime
            ad['no_certificado'] = respuesta['Data']['Timbre']['NoCertificado']
            ad['cfdi_cadena_original'] = respuesta['Data']['Timbre']['CadenaOriginal']
            ad['Sello'] = respuesta['Data']['Timbre']['SelloSAT']
            ad['pac_timbre'] = respuesta['Data']['Timbre']['CFDIPac']
            ad['timbre'] = respuesta['Descripcion']
            ad['cfdi_cadena_original'] = respuesta['Data']['Timbre']['CadenaOriginal']
            ad['sello'] = respuesta['Data']['Timbre']['SelloEmisor']
            xml_recep = respuesta['Data']['Timbre']['Xml'] 
            _logger.error(base64.b64decode(xml_recep))   
            ad['state_sat'] = 'validate' 
            #ad['state'] = 'open'                   
            self.write(ad) 
            
            cfdi['type_document'] = self.tipo_documento_id.name or self.tipo_documento_id_nc.name
            cfdi['fecha_timbrado'] = self.invoice_datetime
            cfdi['cfdi_num_certificado'] = self.compania_emisora_id.serial_number
            cfdi['cfdi_sello'] = respuesta['Data']['Timbre']['SelloEmisor']
            cfdi['cfdi_folio'] = respuesta['Data']['Timbre']['FolioFsical']
            cfdi['cfdi_cadena_original'] = respuesta['Data']['Timbre']['CadenaOriginal']
            cfdi['pac_timbrado'] = respuesta['Data']['Timbre']['CFDIPac']
            cfdi['sello'] = respuesta['Data']['Timbre']['SelloSAT']
            cfdi['certificado'] = respuesta['Data']['Timbre']['NoCertificado']
            cfdi['total_docto'] = self.amount_total
            cfdi['name'] = self.name
            cfdi['rfc_emisor'] = self.compania_emisora_id.rfc
            cfdi['rfc_receptor'] = self.partner_id.rfc
            cfdi['codigo_bm'] = self.create_qr_image(respuesta, self.amount_total)
            cfdi['pac_timbrado'] = respuesta['Data']['Timbre']['CFDIPac']
            cfdi['currency_id'] = self.currency_id.id
            self.env['xmlcfdi'].create(cfdi)         
            self.cfdi_cbb = self.create_qr_image(respuesta, self.amount_total)

            
            xml_dec = base64.decodestring(str.encode(xml_recep))            
            xml_dec= xml_dec.decode("utf-8").replace('\r\n','') 

            attachment_obj = self.env['ir.attachment']   
            
            data_at = {
                        'name': fname_invoice,
                        'datas': base64.encodestring(str.encode(xml_dec)),                        
                        #'datas_fname': fname_invoice,
                        'description': 'Archivo XML del Comprobante Fiscal Digital de la factura',
                        'res_model': 'account.move',
                        'res_id': self.id,
                        'type': 'binary',                        
            }
            attach = attachment_obj.with_context({}).create(data_at)
            xres = self.do_something_with_xml_attachment(attach)

            if self.state_sat == 'validate' and self.partner_id.envio_cfdi:
                msj = _('No se enviaron los archivos por correo porque el Partner está marcado para no enviar automáticamente los archivos del CFDI (XML y PDF)')

            elif self.state_sat == 'validate' and not self.partner_id.envio_cfdi:                
                msj = ''
                state = ''
                partner_mail = self.partner_id.email or False
                user_mail = self.env.user.email or False
                company_id = self.company_id.id                
                address_id = self.partner_id.address_get(['invoice'])['invoice']
                partner_invoice_address = address_id
                fname_invoice = self.name_invoice or ''
                adjuntos = attachment_obj.search([('res_model', '=', 'account.move'), 
                                                  ('res_id', '=', self.id)])
                q = True
                attachments = []
                for attach in adjuntos:
                    if q and attach.name.endswith('.xml'):
                        attachments.append(attach.id)
                        break

                mail_compose_message_pool = self.env['mail.compose.message']                    
                report_ids = self.journal_id.report_id_fact or False

                if report_ids:
                    report_name = report_ids.report_name
                    if report_name:
                        template_id = self.env['mail.template'].search([('model_id.model', '=', 'account.move'),
                                                                         #('company_id','=', company_id),
                                                                         ('name','not ilike', '%Portal%'),], limit=1)                            

                    if template_id:
                        ctx = dict(
                            default_model='account.move',
                            default_res_id=self.id,
                            default_use_template=bool(template_id),
                            default_template_id=template_id.id,
                            default_composition_mode='comment',
                            mark_invoice_as_sent=True,
                        )
                                                 
                        context2 = dict(self._context)
                        if 'default_journal_id' in context2:
                            del context2['default_journal_id']
                        if 'default_type' in context2:
                            del context2['default_type']
                        if 'search_default_dashboard' in context2:
                            del context2['search_default_dashboard']

                        xres = mail_compose_message_pool.with_context(context2)._onchange_template_id(template_id=template_id.id, composition_mode=None,
                                                                                 model='account.move', res_id=self.id)
                        try:
                            try:
                                attachments.append(xres['value']['attachment_ids'][0][2][0])
                            except:
                                mail_attachments = (xres['value']['attachment_ids'])
                                for mail_atch in mail_attachments:
                                    if mail_atch[0] == 4:                                        
                                        attach_br = self.env['ir.attachment'].browse(mail_atch[1])
                                        if attach_br.name != fname_invoice+'.pdf':
                                            attach_br.write({'name': fname_invoice+'.pdf'})
                                        attachments.append(mail_atch[1])
                        except:
                            _logger.error('No se genero el PDF de la Factura, no se enviara al cliente. - Factura: %s', fname_invoice)
                        xres['value'].update({'attachment_ids' : [(6, 0, attachments)]})
                        message = mail_compose_message_pool.with_context(ctx).create(xres['value'])
                        _logger.info('Antes de  enviar XML y PDF por mail al cliente - Factura: %s', fname_invoice)
                        xx = message.action_send_mail()
                        _logger.info('Despues de  enviar XML y PDF por mail al cliente - Factura: %s', fname_invoice)
                        
                        msj = _("La factura fue enviada exitosamente por correo electrónico...")
                        
                    else:
                        msj = _('Advertencia !!!\nRevise que su plantilla de correo esté asignada al Servidor de correo.\nTambién revise que tenga asignado el reporte a usar.\nLa plantilla está asociada a la misma Compañía')
                else:
                    msj = _('No se encontró definido el Reporte de Factura en el Diario Contable !!!\nRevise la configuración')              
                   
            # Se encontraron que los archivos PDF se duplican
            adjuntos2 = attachment_obj.search([('res_model', '=', 'account.move'), ('res_id', '=', self.id)])
            x = 0
            for attach in adjuntos2:
                if attach.name.endswith('.pdf'):
                    x and attach.unlink()
                    if x: 
                        break
                    x += 1
            self.env.cr.commit()
            
        else:            
            if respuesta['Codigo'] == 0:
                raise UserError(_("Error de Timbrado:\n\n %s" % respuesta['Data']['Error']['CodigoError']))
                
            
    def return_index_floats(self,decimales):
        i = len(decimales) - 1
        indice = 0
        while(i > 0):
            if decimales[i] != '0':
                indice = i
                i = -1
            else:
                i-=1
        return  indice   
        #Función para crear el Código Bidimensional#
    @api.model                     
    def create_qr_image(self, values, amount_total):       
        
        url = "https://verificacfdi.facturaelectronica.sat.gob.mx/default.aspx?"
        UUID = self.UUID
        qr_emisor = self.direccion_compañia_id.rfc   
        qr_receptor = self.partner_id.rfc
        total = "%.6f" % ( self.amount_total or 0.0)
        total_qr = ""
        qr_total_split = total.split('.')
        _logger.error("Total factura: %s", qr_total_split)
        decimales = qr_total_split[1]
        index_zero = self.return_index_floats(decimales)
        decimales_res = decimales[0:index_zero+1]
        if decimales_res == '0':
            total_qr = qr_total_split[0]

        else:
            total_qr = qr_total_split[0]+"."+decimales_res
            
        last_8_digits_sello = ""
        
        cfdi_sello =  self.Sello        
        last_8_digits_sello = cfdi_sello[len(cfdi_sello)-8:]         
        qr_string = '%s&id=%s&re=%s&rr=%s&tt=%s&fe=%s'% (url, UUID, qr_emisor, qr_receptor, total_qr, last_8_digits_sello)       
        #try:
        img = qrcode.make(qr_string.encode('utf-8'))
        _logger.error("imagen: %s", img)
        output = io.BytesIO()
        img.save(output, format='JPEG')
        qr_bytes = base64.encodestring(output.getvalue())
        """except:
            raise UserError(_('Advertencia !!!\nNo se pudo crear el Código Bidimensional. Error %s'))"""
        return qr_bytes or False       
    

    #@api.model
    def cancelar_timbre(self):

      fname_xml = self.name_invoice and self.name_invoice + '.xml' or '' 
      webservice_url = self.env['ir.config_parameter'].sudo().get_param('webservice.url')
      if webservice_url == 'test':
          url = self.env['ir.config_parameter'].sudo().get_param('webservice.url_name_prue')
      if webservice_url == 'product':
          url = self.env['ir.config_parameter'].sudo().get_param('webservice.url_name_produc')
      
      data = {
                  "Login": {
                  "rfc": self.env['ir.config_parameter'].sudo().get_param('webservice.rfc_web'),
                  "clave": self.env['ir.config_parameter'].sudo().get_param('webservice.password')
                  },
                  "FoliosUUID": {
                  "FolioUUID": [
                  {
                  "UUID": self.UUID
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
          ad['type_document'] = self.tipo_documento_id.name
          ad['fecha_timbrado'] = self.FechaTimbrado
          ad['cfdi_num_certificado'] = self.compañia_emisora_id.serial_number
          ad['cfdi_sello'] = self.sello
          ad['cfdi_folio'] = self.UUID
          ad['cfdi_cadena_original'] = self.cfdi_cadena_original
          ad['pac_timbrado'] = self.pac_timbre
          ad['sello'] = self.Sello
          ad['certificado'] = self.no_certificado
          ad['total_docto'] = self.amount_total
          ad['factura'] = self.id
          ad['rfc_emisor'] = self.compañia_emisora_id.rfc
          ad['rfc_receptor'] = self.partner_id.rfc           
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
                      #'datas_fname': fname_xml,
                      'description': 'Archivo XML del Acuse de solicitud de cancelación',
                      'res_model': 'cancelaciones',
                      'res_id': result.id,
                      'type': 'binary',                        
          }
          _logger.error('Adjunto: %s', data_at)
          attach = attachment_obj.with_context({}).create(data_at)

          xres = self.with_context(cancelacion = True).do_something_with_xml_attachment(attach)

          """if self.partner_id.envio_cfdi:
              msj = _('No se enviaron los archivos por correo porque el Partner está marcado para no enviar automáticamente los archivos del CFDI (XML y PDF)')

          elif not self.partner_id.envio_cfdi:                
              msj = ''
              state = ''
              partner_mail = self.partner_id.email or False
              user_mail = self.env.user.email or False
              company_id = self.company_id.id                
              address_id = self.partner_id.address_get(['invoice'])['invoice']
              partner_invoice_address = address_id
              fname_invoice = fname_xml or ''
              adjuntos = attachment_obj.search([('res_model', '=', 'cancelaciones'), 
                                                ('res_id', '=', self.cancel_solicitud.id)])
              q = True
              attachments = []
              for attach in adjuntos:
                  if q and attach.name.endswith('.xml'):
                      attachments.append(attach.id)
                      break

              mail_compose_message_pool = self.env['mail.compose.message']                    
              
              template_id = self.env['mail.template'].search([('model_id.model', '=', 'cancelaciones'),
                                                               #('company_id','=', company_id),
                                                               ('name','not ilike', '%Portal%'),], limit=1)                            
              _logger.error('template: %s', template_id)

              if template_id:
                  ctx = dict(
                      default_model='cancelaciones',
                      default_res_id= self.cancel_solicitud.id,
                      default_use_template=bool(template_id),
                      default_template_id=template_id.id,
                      default_composition_mode='comment',
                      mark_invoice_as_sent=True,
                  )
                  _logger.error('contextomend: %s', ctx)                         
                  context2 = dict(self._context)                  
                  if 'default_journal_id' in context2:
                      del context2['default_journal_id']
                  if 'default_type' in context2:
                      del context2['default_type']
                  if 'search_default_dashboard' in context2:
                      del context2['search_default_dashboard']

                  xres1 = mail_compose_message_pool.onchange_template_id(template_id=template_id.id, composition_mode=None,
                                                                           model='cancelaciones', res_id=self.cancel_solicitud.id)
                  try:
                      try:
                          attachments.append(xres1['value']['attachment_ids'][0][2][0])
                      except:
                          mail_attachments = (xres1['value']['attachment_ids'])
                          for mail_atch in mail_attachments:
                              if mail_atch[0] == 4:                                        
                                  attach_br = self.env['ir.attachment'].browse(mail_atch[1])
                                  if attach_br.name != fname_xml+'.xml':
                                      attach_br.write({'name': fname_xml+'.xml'})
                                  attachments.append(mail_atch[1])
                  except:
                      _logger.error('No se genero el PDF de la Factura, no se enviara al cliente. - Factura: %s', fname_xml)
                  xres['value'].update({'attachment_ids' : [(6, 0, attachments)]})
                  message = mail_compose_message_pool.with_context(ctx).create(xres1['value'])
                  _logger.info('Antes de  enviar XML y PDF por mail al cliente - Factura: %s', fname_xml)
                  xx = message.send_mail()
                  _logger.info('Despues de  enviar XML y PDF por mail al cliente - Factura: %s', fname_xml)
                  
                  msj = _("El Acuse fue enviada exitosamente por correo electrónico...")
                  
              else:
                  msj = _('Advertencia !!!\nRevise que su plantilla de correo esté asignada al Servidor de correo.\nTambién revise que tenga asignado el reporte a usar.\nLa plantilla está asociada a la misma Compañía')
          else:
              msj = _('No se encontró definido el Reporte de Factura en el Diario Contable !!!\nRevise la configuración')"""
             
      
      

      self.env.cr.commit()
      return True


            
                



        

