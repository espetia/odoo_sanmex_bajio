# -*- coding: utf-8 -*-
##############################################################################
#
#   Original Author:
#    2014 Agile Business Group sagl
#    (<http://www.agilebg.com>)
#    
#   Forked by:
#   2016 - Argil Consulting SA de CV
#    (<http://www.argil.mx>)
##############################################################################

from odoo import models, fields, api, _
import odoo.addons.decimal_precision as dp
from odoo.exceptions import UserError
import time


class account_subscription_wizard(models.TransientModel):

    _name = "account.subscription.wizard"
    _description = "Subscription Compute"

    date = fields.Date('Generate Entries Before', required=True, default=fields.Date.context_today)


    #@api.model
    def action_generate(self):
        sub_line_obj = self.env['account.subscription.line']
        moves_created=[]
        for data in  self:
            line_ids = sub_line_obj.search([('date', '<', data['date']), ('move_id', '=', False)])
            moves = line_ids.move_create()
            moves_created.extend([x.id for x in moves])        
        
        if not moves_created:
            raise UserError(_('Warning!\nProcess did not return any Account Move. Please check.'))
        
        
        return {
                'domain'    : "[('id','in',[" + ','.join(map(str, list(moves_created))) + "])]",
                'name'      : _('Related Account Moves'),
                'view_mode' : 'tree,form',
                'view_type' : 'form',
                #'context': {'tree_view_ref': 'account.view_move_tree'},
                'res_model' : 'account.move',
                'type'      : 'ir.actions.act_window',
            }

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:      
