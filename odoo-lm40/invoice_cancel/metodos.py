# -*- encoding: utf-8 -*-

from odoo import api, fields, models, _, release
from odoo.exceptions import UserError
import logging
_logger = logging.getLogger(__name__)


class AccountInvoice(models.Model):
    _inherit = "account.move"    

    #@api.model
    def button_cancel_poliza(self):
        date = self._context.get('date', fields.Date.context_today(self))
        account_move_obj = self.env['account.move']
        
        journal_id = ""
        if self.move_type in ('in_invoice', 'in_refound'):
            journal_id = self.env['account.journal'].search([('use_for_invoice_cancel_purchase','=', 1)], limit=1)
        if self.move_type in ('out_invoice', 'out_refound'):
            journal_id = self.env['account.journal'].search([('use_for_invoice_cancel','=', 1)], limit=1)
        for inv in self:
            

            #    continue
            if inv:
                if inv.move_type in ('out_invoice', 'in_invoice'):
                    
                    item_concept = 'item_concept' in ((inv._fields) or {}) and inv.item_concept or False
                    default = { 'date'        : date,
                                'ref'         : _('Cancelación de Factura ') + inv.name,
                                'journal_id'  : journal_id.id,
                                'move_type': 'entry',
                                'tipo_documento_id': 1,
                                }
                    default_origin = { 'date'        : inv.invoice_date,
                                    'ref'         : _('Póliza origina ') + inv.name,
                                    'journal_id'  : journal_id.id,
                                    'move_type': 'entry',
                                    'tipo_documento_id': 1,
                                         }
                    if item_concept:
                        default.update({'item_concept':item_concept})
                    new_move = inv.copy_data(default=default)
                    origin_move = inv.copy_data(default=default_origin)
                    move_id_origin = account_move_obj.create(origin_move[0])
                    move_id_origin.post()
                    for line in new_move[0]['line_ids']:
                        line[2]['debit'], line[2]['credit'] = line[2]['credit'], line[2]['debit']
                        if line[2]['currency_id']:
                            line[2]['amount_currency'] = line[2]['amount_currency'] * -1
                        line[2]['move_id'] and line[2].pop('move_id')
                        line[2]['tax_ids'] and line[2].pop('tax_ids')
                        line[2].update({'journal_id': journal_id.id})
                    _logger.error('lineas: %s', line[2])
                    move_id = account_move_obj.create(new_move[0])
                    move_id.post()
                    move_lines = self.env['account.move.line']
                    move_line_invoice = inv.line_ids.filtered(lambda r: not r.reconciled and r.account_id.internal_type == 'receivable' and r.account_id.internal_type == 'payable')                
                    move_line_cancel  = move_id.line_ids.filtered(lambda r: not r.reconciled and r.account_id.internal_type == 'receivable' and r.account_id.internal_type == 'payable')
                    if 'complement_line_ids' in ((move_line_invoice._fields) or {}) and move_line_invoice.complement_line_ids:
                    
                        default = {'move_line_id' : move_line_cancel.id}
                        for complemento in move_line_invoice.complement_line_ids:
                            res = complemento.copy(default=default)    
                    (move_line_invoice + move_line_cancel).reconcile()
                    
                    inv.write({'original_move_id':move_id_origin.id, 'cancel_move_id': move_id.id})
                    inv.cancel_appply = True
        if self.move_type in ('out_invoice'):
            if self.UUID and self.status_cancel != 'Cancelado':
                raise UserError(_("No puedes crear póliza de reversión una factura con timbre (UUID).\n\nPrimero debes enviar una solicitud de cancelación del CFDI y esperar respuesta."))
            """if not self.UUID and self.state_sat =='no_cfdi':
                raise UserError(_("No puedes crear poliza de reversión una factura no timbrada (UUID), utiliza el botón de Cancelar para realizar este proceso"))"""
        return super(AccountInvoice, self).button_cancel()

    def button_cancel(self):
        res = super(AccountInvoice, self).button_cancel()
        if self.UUID and self.status_cancel != 'Cancelado' :
            raise UserError(_("No puedes cancelar una factura timbrada, Primero debes enviar una solicitud de cancelación del CFDI, esperar respuesta y utilizar la opción de Asiento de Reversión."))
        else:
            return res

    def button_draft(self):
        res = super(AccountInvoice, self).button_draft()
        if self.UUID:
            raise UserError(_("No puedes Cambiar a Borrador una factura timbrada."))
        else: return res

    
class AccountInvoiceCancel(models.TransientModel):
    _inherit = "account_invoice.cancel_wizard"
    
    #@api.model
    def action_cancel(self):
        self.ensure_one()
        
        active_ids = self._context.get('active_ids', []) or []
        if not self.journal_id:

            raise UserError(_("No tiene configurado el Diario Contable a utilizarse cuando se haga Cancelación de Facturas.\n\nEsto lo puede realizar en el la vista de Formulario del Diario Contable."))
          
        #for active in active_ids:
        self.env['account.move'].browse(active_ids).button_cancel_poliza()
        return {'type': 'ir.actions.act_window_close'}
    