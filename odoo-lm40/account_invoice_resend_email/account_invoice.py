# -*- encoding: utf-8 -*-

from odoo import api, fields, models, _, tools
import logging
_logger = logging.getLogger(__name__)


class MailComposer(models.TransientModel):
    _inherit = 'mail.compose.message'
    
    
    #@api.model
    def _onchange_template_id(self, template_id, composition_mode, model, res_id):
        res = super(MailComposer, self)._onchange_template_id(template_id, composition_mode, model, res_id)
        #_logger.error('res: %s', res)
        if model not in ('account.move', 'cancelaciones') or not self._context.get('resend', False):
            return res

        attachment_obj = self.env['ir.attachment']
        rec = self.env[model].browse([res_id])        
        
        attachment_ids = attachment_obj.search([('res_model', '=', model), 
                                                ('res_id', '=', res_id), 
                                                ('name','ilike', model=='account.move' and rec.name_invoice),
                                                ('name','ilike', 'xml'),
                                                ])
        attachment_ids2 = attachment_obj.search([('res_model', '=', model), 
                                                ('res_id', '=', res_id), 
                                                ('name','ilike', model=='account.move' and rec.name_invoice ),
                                                ('name','ilike', 'pdf'),
                                                ], limit=1)                                                
        attachments = [] 
        
        attachments = [attachment1.id for attachment1 in attachment_ids] + [attachment2.id for attachment2 in attachment_ids2]
        res['value']['attachment_ids'] = [(6,0,attachments)]
        return res
        

class AccountInvoice(models.Model):
    _inherit = 'account.move'
    
    #@api.model
    def action_invoice_sent(self):
        res = super(AccountInvoice, self).action_invoice_sent()
        context = res['context']
        context.update({'resend': 1})
        res.update({'context':context})
        return res
class AccountPayment(models.Model):   
    _inherit = 'account.payment'

    #@api.model
    def action_payment_sent(self):
        res = super(AccountPayment, self).action_payment_sent()
        context = res['context']
        context.update({'resend': 1})
        res.update({'context':context})

        return res
