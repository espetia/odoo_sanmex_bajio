# -*- encoding: utf-8 -*-

from odoo import api, fields, models, _
from odoo.exceptions import UserError


class AccountJournal(models.Model):
    _inherit = "account.journal"
    
    
    use_for_invoice_cancel = fields.Boolean(string='Usar al Cancelar Factura Cliente', default=False,
                                            help= 'Si activa la casilla este Diario se usará cuando se creen pólizas de Cancelación de Facturas')
    use_for_invoice_cancel_purchase = fields.Boolean(string='Usar al Cancelar Factura Proveedor', default=False,
                                            help= 'Si activa la casilla este Diario se usará cuando se creen pólizas de Cancelación de Facturas')