

from odoo import api, fields, models, _



class rfc_mx(models.Model):
    _inherit = 'res.partner'

    rfc = fields.Char(string='R.F.C.', size=15, help="RFC de la empresa SIN el prefijo MX")
    



    @api.onchange('rfc', 'country_id')
    def onchange_rfc_sat(self):        
        self.vat = (self.country_id.code or '')+''+(self.rfc or '')
        self.vat_split = self.rfc
        
    