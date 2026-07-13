from odoo import api, fields, models, _
import logging
_logger = logging.getLogger(__name__)
from odoo.exceptions import UserError

class AccountTax(models.Model):
    _inherit = 'account.tax'

    use_tax_cash_basis = fields.Boolean('Aplicar reclasificación en pago')
    tax_cash_basis_account = fields.Many2one('account.account', string='Cuenta de reclasificación', domain=[('deprecated', '=', False),('internal_type','=','other')])
    
    
    #@api.model
    @api.onchange('sat_code_tax')
    def onchange_reclasifica(self):        
        if self.sat_code_tax:
            if self.sat_code_tax.traslado == True:
                self.use_tax_cash_basis = True                
            else:
              self.use_tax_cash_basis = False
        tasa = (self.amount / 100)
        _logger.error('Tasas: %s', tasa)
        if tasa > self.sat_tasa_cuota.value_max:
            raise UserError(_('Advertencia !!!\nLa tasa configurada es mayor a la Permitida'))
