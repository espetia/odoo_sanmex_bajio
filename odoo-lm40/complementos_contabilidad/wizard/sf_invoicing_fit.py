# -*- encoding: utf-8 -*-



from odoo import api, fields, models, _, release
import logging
_logger = logging.getLogger(__name__)

class AccountInvoice(models.Model):
    _inherit = 'account.move'

    @api.model
    def do_something_with_xml_attachment(self, attach):
        self.ensure_one()        
        attachment = attach
        invoice_id = self        
        line_id = [ ln.id for ln in invoice_id.line_ids if ln.account_id.internal_type == (release.major_version in ("10.0","11.0","12.0","13.0","14.0","15.0") and 'receivable') or (release.major_version in ("10.0","11.0","12.0","13.0","14.0","15.0") and "payable") ]
        _logger.error('Contexto: %s', self._context)
        if not 'cancelacion' in self._context:
            if len(line_id):  
                cmplObj = self.env['eaccount.complements']
                _logger.error("Adjuntos: %s", attachment.datas)
                cmpl_vals = cmplObj.onchange_attached(attachment=attachment.datas, currency_id=invoice_id.currency_id)['value']
                _logger.error('Factura complement: %s', cmpl_vals)
                cmpl_vals['type_id'] = self.env['eaccount.complement.types'].search([('key', '=', 'cfdi')], limit=1).id
                cmpl_vals['type_key'] = 'cfdi'
                cmpl_vals['move_line_id'] = line_id[0]
                cmpl_vals['file_data'] = attach.datas
                cmplObj.create(cmpl_vals)         
                resp = invoice_id.write({'item_concept': self.env.user.company_id._assembly_concept(invoice_id.move_type, invoice=invoice_id)})
                _logger.error('Concepto_factura: %s', resp)
        return True




class AccountPayment(models.Model):
    _inherit = 'account.payment'

    @api.model
    def do_something_with_xml_attachment(self, attach):
        self.ensure_one()
        #res = super(AccountPayment, self).do_something_with_xml_attachment(attach)        
        attachment = attach
        #invoice_id = self         
        line_id = [ ln.id for ln in self.payment_move_line_ids if ln.account_id.internal_type == "liquidity" ]
        _logger.error('Valores: %s', line_id)
        if not 'cancelacion' in self._context:
            if len(line_id):            
                cmplObj = self.env['eaccount.complements']
                cmpl_vals = cmplObj.onchange_attached(attachment=attachment.datas, currency_id=self.currency_id)['value']
                _logger.error('complement: %s', cmpl_vals)
                cmpl_vals['type_id'] = self.env['eaccount.complement.types'].search([('key', '=', 'cfdi')], limit=1).id
                cmpl_vals['type_key'] = 'cfdi'
                cmpl_vals['move_line_id'] = line_id[0]
                cmpl_vals['file_data'] = attach.datas            
                cmplObj.create(cmpl_vals)    

            
        return True