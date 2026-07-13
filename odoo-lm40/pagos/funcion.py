# -*- encoding: utf-8 -*-


from odoo import api, fields, models, _, tools
from odoo.exceptions import UserError
import os
import re
import xml
import codecs
import requests
import json
import urllib
import qrcode
import codecs
import operator
import sys
import time
import io
import time as ti
import pytz
import datetime
from datetime import datetime, date
import base64
from odoo.tools import DEFAULT_SERVER_DATETIME_FORMAT, DEFAULT_SERVER_DATE_FORMAT
import logging
_logger = logging.getLogger(__name__)


# Since invoice amounts are unsigned, this is how we know if money comes in or goes out
MAP_INVOICE_TYPE_PAYMENT_SIGN = {
    'out_invoice': 1,
    'in_refund': 1,
    'in_invoice': -1,
    'out_refund': -1,
}


class account_payment(models.Model):
    _inherit = 'account.payment'  
    

    def action_post(self):        
        
        AccountMove = self.env['account.move'].with_context(default_type='entry') 
        diff_currency = self.currency_id != self.company_id.currency_id
        if diff_currency:
            rate = self.env['res.currency.rate'].search([('name','<=',self.date or fields.Date.context_today(self)),('currency_id','=', self.currency_id.id)], order='name desc', limit=1)
            if rate:
                rate.write({'rate': 1/(self.currency_rate or 1.0), 'rate_custom': self.currency_rate or 1.0})

        if 'payment_invoice' in self._context:
            invoice_ids = []
            for payment_inv in self._context['payment_invoice']:
                invoice_ids.append(payment_inv['invoice_id'])
            self.invoice_ids = [(6, 0, invoice_ids)]

        res = super(account_payment, self).action_post()
        payment_line_obj = self.env['account.payment.invoice']        
        for payment in self:
            if payment.payment_type != 'inbound' or not payment.journal_id.use_for_cfdi:
                continue
            monto_aplicado = 0.0
            
            if 'payment_invoice' in self._context:
                for invoice in self.invoice_ids:
                    for payment_inv in self._context['payment_invoice']:
                        if payment_inv['invoice_id'] == invoice.id:
                            data = {'payment_id': self.id,
                                    'invoice_id': invoice.id,
                                    
                                    }
                            #_logger.error('Datos de pago: %s', data)
                            monto_pago = 0.0
                            for ml in invoice.payment_move_line_ids.filtered(lambda r: r.payment_id.id == payment.id):
                                if invoice.currency_id == invoice.company_id.currency_id == payment.currency_id:
                                    monto_pago += (ml.debit + ml.credit)
                                elif ml.currency_id == invoice.currency_id:
                                    monto_pago += abs(ml.amount_currency)
                                else:
                                    monto_pago += payment.currency_id.with_context({'date': ml.date}).compute(abs(ml.amount_currency), invoice.currency_id)
                            
                            last_data = {}
                            
                            for payment_line in invoice.payment_line_ids.filtered(lambda r: r.payment_state not in ['cancel', 'draft']):
                                
                                last_data.update({ payment_line.parcialidad: {'saldo_anterior': payment_line.saldo_anterior, 'monto_pago': payment_line.monto_pago, 'saldo_final': payment_line.saldo_final } })
                                #_logger.error('las_data000: %s', last_data)
                            if last_data:
                                
                                i = max(last_data.items(), key=operator.itemgetter(0))[0]
                                parcialidad = i + 1

                                saldo_anterior = last_data[i]['saldo_final']                                
                                saldo_final = invoice.amount_residual
                                monto_aplicado1 = payment_inv['monto_pago']

                            else:
                                #_logger.info('pago de facturas')
                                parcialidad = 1
                               
                                saldo_anterior = invoice.amount_residual              
                                
                                saldo_final = invoice.amount_residual - payment_inv['monto_pago']#invoice.amount_residual
                                
                                monto_aplicado1 = payment_inv['monto_pago']
                    
                                #_logger.error("saldo: %s", monto_aplicado1)                                
                                #invoice.amount_residual_signed = invoice.amount_total_signed - (monto_aplicado1 * self.currency_rate)
                            monto_aplicado += monto_aplicado1
                            #_logger.error("monto_aplicado: %s", monto_aplicado)
                            data.update({'parcialidad': parcialidad,
                                         'saldo_anterior': saldo_anterior,
                                         'monto_pago': monto_aplicado1,
                                         'saldo_final': saldo_final,
                                         })   
                            #_logger.error('data: %s', data)                         
                            xres = payment_line_obj.create(data)
                            #invoice.amount_residual_signed = invoice.amount_residual_signed - (monto_aplicado1 * self.currency_rate)

            else:
                #_logger.info('funcion una factura')
                for invoice in self.invoice_ids:
                    data = {'payment_id': self.id,
                            'invoice_id': invoice.id,
                            }
                    monto_pago = 0.0
                    for ml in invoice.payment_move_line_ids.filtered(lambda r: r.payment_id.id == payment.id):
                        if invoice.currency_id == invoice.company_id.currency_id == payment.currency_id:
                            monto_pago += (ml.debit + ml.credit)
                        elif ml.currency_id == invoice.currency_id:
                            monto_pago += abs(ml.amount_currency)
                        else:
                            monto_pago += payment.currency_id.with_context({'date': ml.date}).compute(
                                abs(ml.amount_currency), invoice.currency_id)

                    last_data = {}

                    for payment_line in invoice.payment_line_ids.filtered(lambda r: r.payment_id.state not in ('cancelled', 'draft')):
                        last_data.update({payment_line.parcialidad: {'saldo_anterior': payment_line.saldo_anterior, 'monto_pago': payment_line.monto_pago, 'saldo_final': payment_line.saldo_final}})

                    if last_data:
                        #_logger.error('las_data: %s', last_data)
                        i = max(last_data.items(), key=operator.itemgetter(0))[0]
                        parcialidad = i + 1
                        saldo_anterior = last_data[i]['saldo_final']
                        saldo_final = saldo_anterior - payment.amount #( (monto_pago - monto_aplicado) > saldo_anterior and saldo_anterior or (  monto_pago - monto_aplicado))
                        monto_aplicado1 = payment.amount
                        #invoice.amount_residual_signed = invoice.amount_residual #((monto_pago - monto_aplicado) > saldo_anterior and saldo_anterior or (  monto_pago - monto_aplicado))
                    else:
                        parcialidad = 1


                        if invoice.currency_id != payment.currency_id:
                            saldo_anterior = invoice.amount_total#                          
                            rate = round(invoice.currency_id.rate, 6)
                            monto_aplicado1 = payment.amount * rate#invoice.currency_id.rate,
                            #_logger.error("Saldo: %s", monto_aplicado1)
                            saldo_final = saldo_anterior - self.truncate(monto_aplicado1, 2)
                        else:
                            
                            saldo_anterior = invoice.amount_residual
                            saldo_final = invoice.amount_residual - payment.amount                           
                            monto_aplicado1 = payment.amount
                           
                        
                    monto_aplicado += monto_aplicado1

                    data.update({'parcialidad': parcialidad,
                                 'saldo_anterior': saldo_anterior,
                                 'monto_pago': self.truncate(monto_aplicado1, 2),
                                 'saldo_final': saldo_final})
                    #_logger.error('data1: %s', data)
                    xres = payment_line_obj.create(data)           
            
            if payment.timbrar and not payment.timbre_pago():
                raise UserError(_('Advertencia !!!\nOcurrió un error al intentar obtener el CFDI de Recepción de Pagos para el Pago: %s') % (payment.name))    
        return True
            
    def truncate(self, number, decimals=0):
        """
        Returns a value truncated to a specific number of decimal places.
        """
        if not isinstance(decimals, int):
            raise TypeError("decimal places must be an integer.")
        elif decimals < 0:
            raise ValueError("decimal places has to be 0 or more.")
        elif decimals == 0:
           return math.trunc(number)

        factor = 10.0 ** decimals
        return math.trunc(number * factor) / factor 
            
        



    @api.model
    def create(self, vals):
        res = super(account_payment, self).create(vals)
        _logger.info("res: %s", res.reconciled_invoice_ids)
        if res.reconciled_invoice_ids:
            _logger.info("entra aqui 2")          
            
            for invoice in res.reconciled_invoice_ids:
                _logger.info("entra aqui")
                
                    
                nbr_payment = 0
                pay_term_line_ids = invoice.line_ids.filtered(lambda line: line.account_id.user_type_id.type in ('receivable', 'payable'))
                partials = pay_term_line_ids.mapped('matched_debit_ids') + pay_term_line_ids.mapped('matched_credit_ids')
                for partial in partials:
                    counterpart_lines = partial.debit_move_id + partial.credit_move_id
                    counterpart_line = counterpart_lines.filtered(lambda line: line not in invoice.line_ids)
                    if counterpart_line:
                        nbr_payment += 1
                        
                   
        return res

   

    
    


    @api.model
    def do_something_with_xml_attachment(self, attach):

        return True
    
    def timbre_pago(self):
        _logger.error('estafuncion en 4.0')
        
        login ={}
        webservice_url = self.env['ir.config_parameter'].sudo().get_param('webservice.url')
        webservice_url = self.env['ir.config_parameter'].sudo().get_param('webservice.url')
        multi_company = self.env['ir.config_parameter'].sudo().get_param('webservice.multi_company')
        if multi_company == False:
           
            login = {
            "rfc": self.env['ir.config_parameter'].sudo().get_param('webservice.rfc_web'),
            "clave": self.env['ir.config_parameter'].sudo().get_param('webservice.password')
            }
        else:
            #_logger.info('condición aceptada')
            login = {
            "rfc": self.company_id.rfc_web_1,
            "clave": self.company_id.password_1
            }
        if webservice_url == 'test':
            url = self.env['ir.config_parameter'].sudo().get_param('webservice.url_name_prue')
        if webservice_url == 'product':
            url = self.env['ir.config_parameter'].sudo().get_param('webservice.url_name_produc')
        
        fname_payment = self.fname_payment and self.fname_payment + \
                            '.xml' or ''
        pagos = []
        totales = {}
        total_pagos = 0.0
        monto_base = 0.0
        TipoCambioDRdr = 0.0
        monto = 0.0
        monto_im = 0.0
        monto_im_t = 0.0
        monto_t = 0.0
        monto_redondeado = 0.0
        monto_imp_redondeado = 0.0
        monto_im_total = 0.0
        monto_total = 0.0
        monto_impuesto_p = 0.0
        monto_impuesto = 0.0
        monto_base_p = 0.0
        account_tax_obj = self.env['account.tax']

        for payment in self.payment_invoice_line_ids:
            if payment.invoice_currency_id.name != 'MXN':
                tipocambio =  "%.2f" % (self.currency_rate)
            #else:
            if payment.invoice_currency_id.name == 'MXN':
                tipocambio = 1#int(self.currency_rate)
            if not payment.invoice_uuid:
                raise UserError(_('Advertencia !!\nNo se puede generar complemento...la factura no esta timbrada'))            
            
            #if payment.monto_pago == payment.saldo_anterior and payment.parcialidad == 1:
            #uso_cfdi = self.partner_id.uso_cfdi_id.code
            impuestosp = {}
            line_dict_impuestos_t = []
            line_dict_impuestos_r = []
            line_dict_impuestos_t_p = []
            line_dict_impuestos_r_p = []
            if payment.invoice_currency_id == payment.payment_currency_id:
                _logger.error('impuestosfactura: %s', payment.invoice_id.tax_line_ids)
                if payment.invoice_id.tax_line_ids:
                    for tax_dr in payment.invoice_id.tax_line_ids:                     
                        monto_base = payment.monto_pago/(1 + (abs(tax_dr.tax_id.amount/100)))
                        monto_impuesto = monto_base * (tax_dr.tax_id.amount/100)                       
                        if tax_dr.amount < 0:                           
                            line_dict_impuestos_r.append( {                                       
                                                 
                                                  "BaseDR": "%.2f" % (monto_base),
                                                  "ImporteDR": "%.2f" % (abs(monto_base * (tax_dr.tax_id.amount/100))),
                                                  "ImpuestoDR": tax_dr.tax_id.sat_code_tax.code,
                                                  "TasaOCuotaDR": "%.6f" % (abs(tax_dr.tax_id.amount/100)),
                                                  "TipoFactorDR": tax_dr.tax_id.sat_tipo_factor_id.name
                                                   }
                                                  
                                                                                              
                                              )
                        else:
                            monto_base_t = payment.monto_pago/(1 + (abs(tax_dr.tax_id.amount/100)))
                            monto_impuesto_tras = monto_base_t * (tax_dr.tax_id.amount/100)   
                            _logger.error('monto_impuesto_t: %s', monto_impuesto_tras)
                            if tax_dr.tax_id.sat_tipo_factor_id.name != "Exento":                                    
                                   
                                line_dict_impuestos_t.append( {                                                        
                                                     
                                                        
                                                          "BaseDR": "%.2f" % (monto_base),
                                                          "ImporteDR": "%.2f" % (monto_base * (tax_dr.tax_id.amount/100)),
                                                          "ImpuestoDR": tax_dr.tax_id.sat_code_tax.code,
                                                          "TasaOCuotaDR": "%.6f" % (tax_dr.tax_id.amount/100),
                                                          "TipoFactorDR": tax_dr.tax_id.sat_tipo_factor_id.name
                                                        }
                                                      

                                                    )
                            else:
                                line_dict_impuestos_t.append( {                                                        
                                                      
                                                        
                                                          "BaseDR": "%.2f" % (monto_base),                                                  
                                                          "ImpuestoDR": tax_dr.tax_id.sat_code_tax.code,                                                  
                                                          "TipoFactorDR": tax_dr.tax_id.sat_tipo_factor_id.name
                                                        }
                                                      
                                                     
                                                  ) 
                    line_dict = {
                                "EquivalenciaDR": "1",
                                "Folio": payment.invoice_folio,
                                "IdDocumento": payment.invoice_uuid,
                                "ImpPagado": "%.2f" % (payment.monto_pago or 0.0),
                                "ImpSaldoAnt": "%.2f" % (payment.saldo_anterior or 0.0),
                                "ImpSaldoInsoluto": "%.2f" % (payment.saldo_final or 0.0),                                
                                "MonedaDR": payment.invoice_currency_id.name,
                                "NumParcialidad": payment.parcialidad,
                                "Serie": payment.invoice_folio and payment.invoice_folio.replace('/','').replace(' ','').replace('-','') or '',
                                "ObjetoImpDR": "02",
                                "ImpuestosDR": {
                                                "RetencionesDR":{

                                                 "RetencionDR": line_dict_impuestos_r
                                                },
                                                "TrasladosDR": {

                                                 "TrasladoDR": line_dict_impuestos_t 
                                                    }
                                            }
                                                

                                 }
                else:
                    line_dict_impuestos_t = []
                    line_dict_impuestos_r = []
                    line_dict = {
                                "EquivalenciaDR": "1",
                                "Folio": payment.invoice_folio,
                                "IdDocumento": payment.invoice_uuid,
                                "ImpPagado": "%.2f" % (payment.monto_pago or 0.0),
                                "ImpSaldoAnt": "%.2f" % (payment.saldo_anterior or 0.0),
                                "ImpSaldoInsoluto": "%.2f" % (payment.saldo_final or 0.0),                                
                                "MonedaDR": payment.invoice_currency_id.name,
                                "NumParcialidad": payment.parcialidad,
                                "Serie": payment.invoice_folio and payment.invoice_folio.replace('/','').replace(' ','').replace('-','') or '',
                                "ObjetoImpDR": "01",
                                "ImpuestosDR": {
                                                "RetencionesDR":{

                                                 "RetencionDR": line_dict_impuestos_r
                                                },
                                                "TrasladosDR": {

                                                 "TrasladoDR": line_dict_impuestos_t 
                                                    }
                                            }
                                                

                                 }
            if payment.invoice_currency_id != payment.payment_currency_id:
                for tax_dr in payment.invoice_id.tax_line_ids:                    
                    if tax_dr: 
                        monto_base = payment.monto_pago/(1 + (tax_dr.tax_id.amount/100)) 
                        monto_impuesto = monto_base * (tax_dr.tax_id.amount/100)                      
                        if tax_dr.amount < 0:                           
                            line_dict_impuestos_r.append( {
                                              
                                              
                                             
                                              "BaseDR": "%.2f" % (monto_base),
                                              "ImporteDR": "%.2f" % (abs(monto_base * (tax_dr.tax_id.amount/100))),
                                              "ImpuestoDR": tax_dr.tax_id.sat_code_tax.code,
                                              "TasaOCuotaDR": "%.6f" % (tax_dr.tax_id.amount/100),
                                              "TipoFactorDR": tax_dr.tax_id.sat_tipo_factor_id.name
                                               }
                                              
                                                                                          
                                          )
                        else:
                            if tax_dr.tax_id.sat_tipo_factor_id.name != "Exento":                                    
                                #monto_base = payment.monto_pago/(1 + (tax_dr.tax_id.amount/100))
                                line_dict_impuestos_t.append( {                                                        
                                                 
                                                    
                                                      "BaseDR": "%.2f" % (monto_base),
                                                      "ImporteDR": "%.2f" % (monto_base * (tax_dr.tax_id.amount/100)),
                                                      "ImpuestoDR": tax_dr.tax_id.sat_code_tax.code,
                                                      "TasaOCuotaDR": "%.6f" % (tax_dr.tax_id.amount/100),
                                                      "TipoFactorDR": tax_dr.tax_id.sat_tipo_factor_id.name
                                                    }
                                                  

                                                )
                            else:
                                line_dict_impuestos_t.append( {                                                        
                                                  
                                                    
                                                      "BaseDR": "%.2f" % (monto_base),                                                  
                                                      "ImpuestoDR": tax_dr.tax_id.sat_code_tax.code,                                                  
                                                      "TipoFactorDR": tax_dr.tax_id.sat_tipo_factor_id.name
                                                    }
                                                  
                                                 
                                              ) 
                self.currency_rate = ""
                rate = payment.invoice_id.currency_id.with_context(date=self.payment_date or fields.Date.context_today(self))                
                TipoCambioDRdr = '%.10f' % (1/rate.rate_custom)                
                line_dict = {
                                "EquivalenciaDR": TipoCambioDRdr,
                                "Folio": payment.invoice_folio,
                                "IdDocumento": payment.invoice_uuid,
                                "ImpPagado": "%.2f" % (payment.monto_pago or 0.0),
                                "ImpSaldoAnt": "%.2f" % (payment.saldo_anterior or 0.0),
                                "ImpSaldoInsoluto": "%.2f" % (payment.saldo_final or 0.0),                                
                                "MonedaDR": payment.invoice_currency_id.name,
                                "NumParcialidad": payment.parcialidad,
                                "Serie": payment.invoice_folio and payment.invoice_folio.replace('/','').replace(' ','').replace('-','') or '',
                                "ObjetoImpDR": "02",
                                "ImpuestosDR": {
                                            "RetencionesDR":{

                                             "RetencionDR": line_dict_impuestos_r
                                            },
                                            "TrasladosDR": {

                                             "TrasladoDR": line_dict_impuestos_t 
                                                }
                                        }
                                            
                                                

                                 }
            

            
            if payment.invoice_currency_id != payment.payment_currency_id:
                total_pagos_conver = self.amount 
            else:
                total_pagos += payment.monto_pago
                total_pagos_conver = total_pagos * float(tipocambio) 



            

            totales ={
                    "MontoTotalPagos": "%.2f" % (float(total_pagos_conver)),
                    "TotalRetencionesIEPS": "",
                    "TotalRetencionesISR": "",
                    "TotalRetencionesIVA": "",
                    "TotalTrasladosBaseIVA0": "",
                    "TotalTrasladosBaseIVA16": "",
                    "TotalTrasladosBaseIVA8": "",
                    "TotalTrasladosBaseIVAExento": "",
                    "TotalTrasladosImpuestoIVA0": "",
                    "TotalTrasladosImpuestoIVA16": "",
                    "TotalTrasladosImpuestoIVA8": ""
                    }
            for tax_total in payment.invoice_id.tax_line_ids:
                if payment.invoice_currency_id != payment.payment_currency_id:
                    #total_pagos_conver = self.amount                
                    monto_redondeado_t = "%.2f" % (monto_base)
                    monto_impuesto_t = "%.2f" % (float(monto_redondeado_t) * (tax_dr.tax_id.amount/100))

                    monto_im_t += float(monto_impuesto_t) / float(TipoCambioDRdr)

                    monto_t += float(monto_redondeado_t) / float(TipoCambioDRdr)


                else:
                    if tax_total.tax_id.amount < 0:

                                       
                        monto_redondeado_t = "%.2f" % (monto_base)
                        monto_impuesto_t = "%.2f" % (monto_impuesto)
                        monto_t += float(monto_redondeado_t) * float(tipocambio)
                        monto_im_t += float(monto_impuesto_t) * float(tipocambio)
                    else:
                                       
                        monto_redondeado_t = "%.2f" % (monto_base_t)
                        monto_impuesto_t = "%.2f" % (monto_impuesto_tras)
                        monto_t += float(monto_redondeado_t) * float(tipocambio)
                        monto_im_t += float(monto_impuesto_t) * float(tipocambio)
                 
                if tax_total:  
                    _logger.info("impuestototal")  
                    if tax_total.tax_id.amount == 16.0:
                        _logger.info("impuesto 16")
                        
                        totales['TotalTrasladosBaseIVA16'] = "%.2f" % (monto_t)
                        totales['TotalTrasladosImpuestoIVA16'] = "%.2f" % (monto_im_t)#(monto_base_total * (tax_total.tax_id.amount/100))
                    if tax_total.tax_id.amount == 8.0:
                        totales['TotalTrasladosBaseIVA8'] = "%.2f" % (monto_t)
                        totales['TotalTrasladosImpuestoIVA8.0'] = "%.2f" % (monto_im_t)
                    if tax_total.tax_id.tax_category_id.name == 'IVA-TASA CERO':
                        totales['TotalTrasladosBaseIVA0'] = "%.2f" % (monto_t)
                        totales['TotalTrasladosImpuestoIVA0'] = "%.2f" % (monto_im_t)
                    if tax_total.tax_id.tax_category_id.name == 'IVA-EXENTO':
                        totales['TotalTrasladosBaseIVAExento'] = "%.2f" % (monto_t)                        
                    if tax_total.tax_id.tax_category_id.name == 'IVA-RET':
                        monto_base_total = total_pagos_conver / (1 + (abs(tax_total.tax_id.amount/100)))
                        totales['TotalRetencionesIVA'] ="%.2f" % abs((monto_base_total * (tax_total.tax_id.amount/100)))
                    if tax_total.tax_id.tax_category_id.name == 'ISR-RET':
                        totales['TotalRetencionesISR'] = "%.2f" % (monto_t)
                    if tax_total.tax_id.tax_category_id.name == 'IEPS':
                        totales['TotalRetencionesIEPS'] = "%.2f" % (monto_t)            
                
                    
                    if tax_total.tax_id.amount < 0:                         
                        
                        monto_base_p = payment.monto_pago /(1 + (abs(tax_total.tax_id.amount/100)))
                        
                        line_dict_impuestos_r_p.append( {
                                          
                                          
                                        
                                          
                                          "ImporteP": "%.2f" % (abs(monto_base_p * (tax_total.tax_id.amount/100))),
                                          "ImpuestoP": tax_total.tax_id.sat_code_tax.code,
                                          
                                          
                                          }
                                                                                      
                                      )
                    else:
                        if tax_total.tax_id.sat_tipo_factor_id.name != 'Exento':      
                            if payment.invoice_currency_id != payment.payment_currency_id:
                                monto_redondeado = "%.2f" % (monto_base)
                                monto_imp_redondeado = "%.2f" % (monto_impuesto)
                                #monto_redondeado = monto_redondeado
                                _logger.error('montyo base: %s', monto_redondeado)

                                monto_impuesto_p +=  float(monto_imp_redondeado) / float(TipoCambioDRdr)

                                monto += float(monto_redondeado) / float(TipoCambioDRdr)
                                _logger.error('impuestopago: %s', monto)

                                line_dict_impuestos_t_p.append( {  
                                                  
                                             
                                               
                                                  "BaseP": "%.6f" % (monto),
                                                  "ImporteP": "%.6f" % (monto_impuesto_p),
                                                  "ImpuestoP": tax_total.tax_id.sat_code_tax.code,
                                                  "TasaOCuotaP": "%.6f" % (tax_total.tax_id.amount/100),
                                                  "TipoFactorP": tax_total.tax_id.sat_tipo_factor_id.name
                                                }
                                              

                                            )
                            else:

                                monto_redondeado = "%.2f" % (monto_base_t)
                                monto_imp_redondeado = "%.2f" % (float(monto_impuesto_tras))
                                monto_impuesto_p +=  float(monto_imp_redondeado)
                                monto +=  float(monto_redondeado)
                                

                                line_dict_impuestos_t_p.append( {  
                                                      
                                                 
                                                   
                                                      "BaseP": "%.2f" % (abs(monto)),
                                                      "ImporteP": "%.2f" % (abs(monto_impuesto_p)),
                                                      "ImpuestoP": tax_total.tax_id.sat_code_tax.code,
                                                      "TasaOCuotaP": "%.6f" % (tax_total.tax_id.amount/100),
                                                      "TipoFactorP": tax_total.tax_id.sat_tipo_factor_id.name
                                                    }
                                                  

                                                )
                        else:
                            line_dict_impuestos_t_p.append( {  
                                                  
                                              
                                               
                                                  "BaseP": "%.2f" % (monto),                                                  
                                                  "ImpuestoP": tax_total.tax_id.sat_code_tax.code,                                                  
                                                  "TipoFactorP": tax_total.tax_id.sat_tipo_factor_id.name
                                                }
                                              
                                             
                                          ) 
                else:
                    line_dict_impuestos_t_p = []
                    line_dict_impuestos_r_p = []


            impuestosp = {
                            "RetencionesP": {
                                "RetencioneP": line_dict_impuestos_r_p

                            },
                            
                             "TrasladosP": {
                                "TrasladoP": line_dict_impuestos_t_p
                                

                             }
                             }

            pagos.append(line_dict)
        
        ###Validaciones para emisor y receptor####
        
        
        if not self.partner_id.rfc:
            raise UserError(_('Advertencia !!\nNo ha definido el RFC de la Compañía...'))        
        if self.timbrar == True:
                if self.invoice_ids.cancel_solicitud:
                    raise UserError(_('Advertencia !!!\nNo puede registrar pago debido a que cuenta con una solicitud de Cancelación'))
        if self.UUID: 
               
            raise UserError(_('Advertencia !!!\nEl pago ya se encuentra Timbrado'))
        

        tz = self.with_context(tz=self.env.user.partner_id.tz)             
        #fecha = fields.Datetime.now()      
        fecha = self.payment_datetime_reception  
        fecha = fields.Datetime.context_timestamp(tz, fields.Datetime.from_string(fecha))        
        fecha = ti.strftime('%Y-%m-%dT%H:%M:%S', ti.strptime(str(fecha)[0:19], '%Y-%m-%d %H:%M:%S'))
        fecha_timbre = fields.Datetime.now()
        fecha_timbre = fields.Datetime.context_timestamp(tz, fields.Datetime.from_string(fecha_timbre))        
        fecha_timbre = ti.strftime('%Y-%m-%dT%H:%M:%S', ti.strptime(str(fecha_timbre)[0:19], '%Y-%m-%d %H:%M:%S'))
        #_logger.error('fecha_timbre: %s', fecha_timbre)
        
        
        producto_pago = self.env['ir.config_parameter'].sudo().get_param('webservice.producto_pago')
        producto_pago = self.env['product.product'].browse(int(producto_pago)).exists()        
        #_logger.error('producto_pago: %s', producto_pago)
        producto = str(producto_pago.name).encode("utf-8")       
        #_logger.error('producto: %s', producto)
        base64_dato = base64.b64encode(producto)
        producto_dec = base64_dato.decode("utf-8")

        base64_dato = base64.b64encode(producto)
        producto_dec = base64_dato.decode("utf-8")

        rfc_emisor = self.company_emitter_id.rfc
        rfc_emis = str(rfc_emisor).encode("utf-8")
        base64_rfc = base64.b64encode(rfc_emis)
        rfc_dec = base64_rfc.decode("utf-8")

        rfc_receptor = self.partner_id.rfc
        rfc_recep = str(rfc_receptor).encode("utf-8")
        base64_rfc_recep = base64.b64encode(rfc_recep)
        rfc_dec_recep = base64_rfc_recep.decode("utf-8")

        name_emisor = self.company_emitter_id.name
        name_emi = str(name_emisor).encode("utf-8")
        base64_name_clie = base64.b64encode(name_emi)
        name_emi_dec = base64_name_clie.decode("utf-8")

        name_receptor = self.partner_id.name
        name_rec = str(name_receptor).encode("utf-8")
        base64_name_recp = base64.b64encode(name_rec)
        name_rec_dec = base64_name_recp.decode("utf-8")

        timbrar_pago ={
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
                                    "Pago": [
                                        {
                                            #"CadPago": "",
                                            #"CertPago": "",
                                            #"CtaBeneficiario": "",
                                            #"CtaOrdenante": "",
                                            "DoctoRelacionado": pagos,
                                            "FechaPago": fecha,
                                            "FormaDePagoP":self.pay_method_id.code,
                                            "ImpuestosP": impuestosp,
                                            "MonedaP": self.currency_id.name,
                                            "Monto": "%.2f" % (self.amount or 0.0),
                                            #"NomBancoOrdExt": "",
                                            "NumOperacion": self.num_operacion or '',
                                            #"RfcEmisorCtaBen": "",
                                            #"RfcEmisorCtaOrd": "",
                                            #"SelloPago": "",
                                            #"TipoCadPago": "",
                                            "TipoCambioP": tipocambio
                                        }
                                    ],
                                    "Totales": totales,
                                    "Version": 2.0
                                },
                                "TimbreFiscalDigital": {
                                    "FechaTimbrado": "",
                                    "NoCertificadoSAt": "",
                                    "RfcProvCertif": "",
                                    "SelloCFD": "",
                                    "SelloSAT": "",
                                    "TimbreFiscalDigital": "",
                                    "UUID": "",
                                    "Version": 4.0
                                }
                            },
                            "Conceptos": {
                                "Concepto": [
                                    {
                                        "Cantidad": 1,
                                        "ObjetoImp" : "01",
                                        "ClaveProdServ": (producto_pago)[0].sat_product_id.code,
                                        "ClaveUnidad": (producto_pago)[0].uom_id.sat_uom_id.code,
                                        "CuentaPredial": {
                                            "Numero": ""
                                        },
                                        "Descripcion": producto_dec,
                                        "Descuento": 0,
                                        "Importe": 0,
                                        "Impuestos": {
                                            "Retenciones": [],
                                            "Traslados": []
                                        },
                                        "InformacionAduanera": {
                                            "NumeroPedimento": ""
                                        },
                                        "NoIdentificacion": "",
                                        "Parte": {
                                            "Parte": {
                                                "Concepto": []
                                            }
                                        },
                                        "Unidad": "",
                                        "Valorunitario": 0
                                    }
                                ]
                            },
                            "CondicionesDePago": "",
                            "Confirmacion": "",
                            "Descuento": "",
                            "Emisor": {
                                "Nombre": name_emi_dec,
                                "RegimenFiscal": self.address_issued_id.regimen_fiscal_id.code,
                                "Rfc": rfc_dec
                            },
                            "Fecha":fecha_timbre,
                            "Folio": "",
                            "FormaPago": "",
                            "Exportacion": "01",
                            "Impuestos": {
                                "Retenciones": [],
                                "TotalImpuestosRetenidos": "",
                                "TotalImpuestosTrasladados": "",
                                "Traslados": []
                            },
                            "LugarExpedicion": self.address_issued_id.sat_codigopostal_id.code,
                            "MetodoPago": "",
                            "Moneda": "XXX",
                            "NoCertificado": "",
                            "Pagos": {
                                "Pago": []
                            },
                            "Receptor": {
                                "Nombre": name_rec_dec,
                                "NumRegIdTrib": "",
                                "ResidenciaFiscal": "",
                                "Rfc": rfc_dec_recep,
                                "RegimenFiscalReceptor": self.partner_id.regimen_fiscal_id.code,                    
                                "DomicilioFiscalReceptor":self.partner_id.sat_codigopostal_id.code,
                                "UsoCFDI": "CP01"
                            },
                            "Sello": "",
                            "Serie": self.name.replace('/','').replace(' ','').replace('-','') or '',
                            "Subtotal": 0.0,
                            "TipoCambio": tipocambio,
                            "TipoDeComprobante": "P",
                            "Total": 0.0,
                            "Version": 4.0
                        },
                        "Operacion": "",
                        "TipoDocumento": ""
                    },
                    "Login": login,
                }
            }
        _logger.error('Datos enviados: %s', timbrar_pago)



       
        datos_cod = str(timbrar_pago).encode('utf-8')
        base64_datos = base64.b64encode(datos_cod)
        cadena = ""
        cadena = base64_datos.decode("utf-8")
        cadena_data = cadena
        data = {

               "datos":cadena_data
                

               }
        #_logger.error("Base 64: %s", data)
        headers = {'content-type': 'application/json'}
        resp = requests.post(str(url) + "/Timbrar/CFDI", data=json.dumps(data), headers=headers)
        respuesta = json.loads(resp.content.decode("utf-8"))
        _logger.error('respuesta: %s', respuesta)

        xml_recep = ""
        ad = dict()
        cfdi = dict()
        if respuesta['Codigo'] == 1:
            ad['UUID'] = respuesta['Data']['Timbre']['FolioFsical']
            ad['fecha_timbrado'] = fields.Datetime.now()#self.payment_datetime_reception
            ad['cfdi_no_certificado'] = respuesta['Data']['Timbre']['NoCertificado']
            ad['cfdi_cadena_original'] = respuesta['Data']['Timbre']['CadenaOriginal']
            ad['cfdi_sello'] = respuesta['Data']['Timbre']['SelloSAT']
            ad['pac_timbre'] = respuesta['Data']['Timbre']['CFDIPac']            
            ad['cfdi_cadena_original'] = respuesta['Data']['Timbre']['CadenaOriginal']
            ad['sello'] = respuesta['Data']['Timbre']['SelloEmisor']
            xml_recep = respuesta['Data']['Timbre']['Xml']                                
            self.write(ad) 
            
            cfdi['type_document'] = "Pago"
            cfdi['fecha_timbrado'] = fields.Datetime.now()#self.payment_datetime_reception
            cfdi['cfdi_num_certificado'] = self.company_emitter_id.serial_number
            cfdi['cfdi_sello'] = respuesta['Data']['Timbre']['SelloEmisor']
            cfdi['cfdi_folio'] = respuesta['Data']['Timbre']['FolioFsical']
            cfdi['cfdi_cadena_original'] = respuesta['Data']['Timbre']['CadenaOriginal']
            cfdi['pac_timbrado'] = respuesta['Data']['Timbre']['CFDIPac']
            cfdi['sello'] = respuesta['Data']['Timbre']['SelloSAT']
            cfdi['certificado'] = respuesta['Data']['Timbre']['NoCertificado']
            cfdi['total_docto'] = self.amount
            cfdi['name'] = self.name
            cfdi['rfc_emisor'] = self.company_emitter_id.rfc
            cfdi['rfc_receptor'] = self.partner_id.rfc
            cfdi['codigo_bm'] = self.create_qr_image(respuesta, self.amount)
            cfdi['pac_timbrado'] = respuesta['Data']['Timbre']['CFDIPac']
            self.env['xmlcfdi'].create(cfdi)

            self.cfdi_cbb = self.create_qr_image(respuesta, self.amount)

            
            xml_dec = base64.decodestring(str.encode(xml_recep))            
            xml_dec= xml_dec.decode("utf-8").replace('\r\n','') 

            attachment_obj = self.env['ir.attachment']   
            
            data_at = {
                        'name': fname_payment,
                        'datas': base64.encodestring(str.encode(xml_dec)),                        
                        #'datas_fname': fname_payment,
                        'description': 'Archivo XML del Comprobante Fiscal Digital del Pago',
                        'res_model': 'account.payment',
                        'res_id': self.id,
                        'type': 'binary',                        
            }
            attach = attachment_obj.with_context({}).create(data_at)
            xres = self.do_something_with_xml_attachment(attach)
            if self.partner_id.envio_cfdi:
                msj = _('No se enviaron los archivos por correo porque el Partner está marcado para no enviar automáticamente los archivos del CFDI (XML y PDF)')

            elif not self.partner_id.envio_cfdi:                
                msj = ''
                state = ''
                partner_mail = self.partner_id.email or False
                user_mail = self.env.user.email or False
                company_id = self.company_id.id                
                address_id = self.partner_id.address_get(['invoice'])['invoice']
                partner_invoice_address = address_id
                fname_payment = self.fname_payment or ''
                adjuntos = attachment_obj.search([('res_model', '=', 'account.payment'), 
                                                  ('res_id', '=', self.id)])
                q = True
                attachments = []
                for attach in adjuntos:
                    if q and attach.name.endswith('.xml'):
                        attachments.append(attach.id)
                        break

                mail_compose_message_pool = self.env['mail.compose.message']                    
                report_ids = self.journal_id.report_id_pay or False

                if report_ids:
                    report_name = report_ids.report_name
                    if report_name:
                        template_id = self.env['mail.template'].search([('model_id.model', '=', 'account.payment'),                                                                                                     
                                                                        ('report_template.report_name', '=', report_name)], limit=1)
                    if template_id:
                        ctx = dict(
                            default_model='account.payment',
                            default_res_id=self.id,
                            default_use_template=bool(template_id),
                            default_template_id=template_id.id,
                            default_composition_mode='comment',
                            
                        )
                                                 
                        context2 = dict(self._context)
                        if 'default_journal_id' in context2:
                            del context2['default_journal_id']
                        if 'default_type' in context2:
                            del context2['default_type']
                        if 'search_default_dashboard' in context2:
                            del context2['search_default_dashboard']

                        xres = mail_compose_message_pool.with_context(context2)._onchange_template_id(template_id=template_id.id, composition_mode=None,
                                                                                 model='account.payment', res_id=self.id)
                        try:
                            try:
                                attachments.append(xres['value']['attachment_ids'][0][2][0])
                            except:
                                mail_attachments = (xres['value']['attachment_ids'])
                                for mail_atch in mail_attachments:
                                    if mail_atch[0] == 4:                                        
                                        attach_br = self.env['ir.attachment'].browse(mail_atch[1])
                                        if attach_br.name != fname_payment+'.pdf':
                                            attach_br.write({'name': fname_payment+'.pdf'})
                                        attachments.append(mail_atch[1])
                        except:
                            _logger.error('No se genero el PDF de la Factura, no se enviara al cliente. - Factura: %s', fname_invoice)
                        xres['value'].update({'attachment_ids' : [(6, 0, attachments)]})
                        message = mail_compose_message_pool.with_context(ctx).create(xres['value'])
                        _logger.info('Antes de  enviar XML y PDF por mail al cliente - Pago: %s', fname_payment)
                        xx = message.action_send_mail()
                        _logger.info('Despues de  enviar XML y PDF por mail al cliente - Pago: %s', fname_payment)
                        
                        msj = _("El Complemnto fue enviado exitosamente por correo electrónico...")
                        
                    else:
                        msj = _('Advertencia !!!\nRevise que su plantilla de correo esté asignada al Servidor de correo.\nTambién revise que tenga asignado el reporte a usar.\nLa plantilla está asociada a la misma Compañía')
                else:
                    msj = _('No se encontró definido el Reporte de Pagos en el Diario Contable !!!\nRevise la configuración')              
                   
            # Se encontraron que los archivos PDF se duplican
            adjuntos2 = attachment_obj.search([('res_model', '=', 'account.payment'), ('res_id', '=', self.id)])
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
        return True

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
        qr_emisor = self.company_emitter_id.rfc   
        qr_receptor = self.partner_id.rfc
        total = "%.6f" % ( self.amount or 0.0)
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
        
        cfdi_sello =  self.cfdi_sello        
        last_8_digits_sello = cfdi_sello[len(cfdi_sello)-8:]         
        qr_string = '%s&id=%s&re=%s&rr=%s&tt=%s&fe=%s'% (url, UUID, qr_emisor, qr_receptor, total_qr, last_8_digits_sello)       
        
        img = qrcode.make(qr_string.encode('utf-8'))
        _logger.error("imagen: %s", img)
        output = io.BytesIO()
        img.save(output, format='JPEG')
        qr_bytes = base64.encodestring(output.getvalue())
        
        return qr_bytes or False



    @api.model
    def cancel_pago(self):

      fname_payment = self.fname_payment and self.fname_payment + \
                            '.xml' or ''
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
          ad['type_document'] = self.ticomprobante.name
          ad['fecha_timbrado'] = self.fecha_timbrado
          ad['cfdi_num_certificado'] = self.company_emitter_id.serial_number
          ad['cfdi_sello'] = self.cfdi_sello
          ad['cfdi_folio'] = self.UUID
          ad['cfdi_cadena_original'] = self.cfdi_cadena_original
          ad['pac_timbrado'] = self.pac_timbre
          ad['sello'] = self.sello
          ad['certificado'] = self.no_certificado
          ad['total_docto'] = self.amount
          ad['payment_id'] = self.id
          ad['rfc_emisor'] = self.company_emitter_id.rfc
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
                      'name': fname_payment,
                      'datas': base64.encodestring(str.encode(xml_dec)),                        
                      #'datas_fname': fname_payment,
                      'description': 'Archivo XML del Acuse de solicitud de cancelación',
                      'res_model': 'cancelaciones',
                      'res_id': result.id,
                      'type': 'binary',                        
          }
          _logger.error('Adjunto: %s', data_at)
          attach = attachment_obj.with_context({}).create(data_at)

          xres = self.with_context(cancelacion = True).do_something_with_xml_attachment(attach)       
      return True

   
    
    
    
    
  
        
    
    
