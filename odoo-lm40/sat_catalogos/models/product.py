# -*- coding: utf-8 -*-
from odoo import api, fields, models, _, tools
from datetime import datetime
import time
from dateutil.relativedelta import relativedelta
from odoo.exceptions import UserError, RedirectWarning, ValidationError
import re



# Expresion Regular para el Pedimento #
_estructura_pedimento = re.compile('[0-9]{2}\s{2}[0-9]{2}\s{2}[0-9]{4}\s{2}[0-9]{7}')
_no_identify = re.compile('([A-Z]|[a-z]|[0-9]||Ñ|ñ|!|&quot;|%|&amp;|&apos;| ́|-|:|;|&gt;|=|&lt;|@|_|,|\{|\}|`|~|á|é|í|ó|ú|Á|É|Í|Ó|Ú|ü|Ü){1,100}')


class ProductTemplate(models.Model):
    _name = 'product.template'
    _inherit ='product.template'

    sat_product_id = fields.Many2one('sat.producto','Clave Producto SAT')
    no_identity_type = fields.Selection([('none','No Aplica'),
                                         ('default_code','Referencia Interna'),
                                         ('barcode','Codigo de Barras'),
                                         ('manual','Otro')
                                         ],'Tipo de Identificacion',
                                         default='none')

    no_identity_other = fields.Char('No. Identificacion Manual', size=100)
    account_income = fields.Many2one('account.account', company_dependent=True, string="Ingresos de Contado",
        domain=[('deprecated', '=', False),('internal_type','=','other')])

class ProductUom(models.Model):
    _name = 'uom.uom'
    _inherit ='uom.uom'

    sat_uom_id = fields.Many2one('sat.udm','Clave SAT')

class ProductCategory(models.Model):
    _name = 'product.category'
    _inherit ='product.category'

    sat_product_id = fields.Many2one('sat.producto','Clave Producto SAT')
    account_income = fields.Many2one('account.account', company_dependent=True, string="Ingresos de Contado", 
        domain=[('deprecated', '=', False),('internal_type','=','other')])
        



class AccountTax(models.Model):
    _name = 'account.tax'
    _inherit ='account.tax'

    sat_tasa_cuota = fields.Many2one('sat.tasa.cuota', 'Rango o Fijo')
    sat_tipo_factor_id = fields.Many2one('sat.tipofactor', 'Tipo Factor')   

    sat_code_tax =fields.Many2one('sat.impuesto', string="Clave SAT")
    estimulo_frontera = fields.Boolean('Estímulo')

    
