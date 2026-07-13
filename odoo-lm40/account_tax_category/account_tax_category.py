# -*- encoding: utf-8 -*-

from odoo import api, fields, models, _, tools


class account_tax_category(models.Model):
    _name = 'account.tax.category'

    company_id  = fields.Many2one('res.company', string='Compañía', 
                                default=lambda self: self.env['res.company']._company_default_get('mail.template'))    
    name        = fields.Char(string='Nombre', size=64, required=True)
    code        = fields.Char(string='Código', size=32, required=True)
    active      = fields.Boolean(string='Active', default=1)
    sign        = fields.Integer(string='Signo')
    category_ids= fields.One2many('account.tax', 'tax_category_id', string='Categoría', help='Tax that belong of this category')
    value_tax   = fields.Float(string='Monto')
    

class account_tax(models.Model):
    _inherit = 'account.tax'

    tax_category_id = fields.Many2one('account.tax.category', string='Categoría', required=False)
