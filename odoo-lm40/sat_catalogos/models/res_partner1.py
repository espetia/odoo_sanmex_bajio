# -*- encoding: utf-8 -*-

from odoo import api, fields, models, _
import logging
_logger = logging.getLogger(__name__)

class res_partner(models.Model):
    _inherit = 'res.partner'
    
    
    @api.model
    def _address_fields(self):
        
        return list(('street', 'street2', 'zip', 'city', 'state_id', 'country_id','num_external', 'num_internal', 'city2'))
    
    def _get_default_country_id(self):        
        country_obj = self.env['res.country']
        country = country_obj.search([('code', '=', 'MX'), ], limit=1)
        country_id = country.id or False
        self.country_id = country_id
        _logger.error("arg: %s", country)
        _logger.error("country: %s", country_id)
        return  country and country.id or False
        
    num_external = fields.Char(string='No. External', size=128, help='External number of the partner address')
    num_internal = fields.Char(string='No. Internal', size=128, help='Internal number of the partner address')
    city2 = fields.Char(string='Locality', size=128, help='Locality configurated for this partner')
    country_id = fields.Many2one('res.country', string='Country', ondelete='restrict', default=_get_default_country_id) 
    
    regimen_fiscal_id = fields.Many2one('sat.regimen.fiscal', string="Régimen Fiscal")

    vat_split = fields.Char('VAT Split')    
    pay_method_id = fields.Many2one('pay.method', string='Forma de Pago')
