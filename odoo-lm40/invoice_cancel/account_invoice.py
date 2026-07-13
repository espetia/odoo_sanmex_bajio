# -*- encoding: utf-8 -*-

from odoo import api, fields, models, _
from odoo.exceptions import UserError


class AccountInvoice(models.Model):
    _inherit = "account.move"
    
    
    original_move_id = fields.Many2one('account.move', string='Póliza Original', readonly=True, index=True, 
                                       ondelete='restrict', copy=False,
                                        help="Liga a la póliza contable generada automáticamente.")
    cancel_move_id = fields.Many2one('account.move', string='Póliza de Cancelación', readonly=True, index=True, 
                                      ondelete='restrict', copy=False,
                                      help="Liga a la póliza contable correspondiente a las partidas de cancelación.")
    
    
class AccountInvoiceCancel(models.TransientModel):
    """
    This wizard will try to get Coords for all selected Places
    """

    _name = "account_invoice.cancel_wizard"
    _description = "Wizard para cancelar la Factura"


    @api.model
    def _default_journal(self):
        return self.env['account.journal'].search([('use_for_invoice_cancel','=', 1)], limit=1)
    
    date = fields.Date(string='Fecha Cancelación', default=fields.Date.context_today, required=True, readonly=True,
                        help="Fecha en la que se creará la Póliza de Cancelación de la Factura.")
    journal_id = fields.Many2one('account.journal', string='Diario', required=True, default=_default_journal, readonly=True)
