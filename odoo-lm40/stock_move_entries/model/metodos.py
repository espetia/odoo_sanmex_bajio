# -*- encoding: utf-8 -*-
from odoo.exceptions import UserError, ValidationError
from odoo import api, fields, models, _, release
import odoo.addons.decimal_precision as dp
from odoo.osv import osv


class stock_move(models.Model):
    _inherit = "stock.move"
    
    

    def _prepare_account_move_line(self, qty, cost, credit_account_id, debit_account_id):
        
        self.ensure_one()

        if self._context.get('force_valuation_amount'):
            valuation_amount = self._context.get('force_valuation_amount')
        else:
            valuation_amount = cost

        if self._context.get('forced_ref'):
            ref = self._context['forced_ref']
        else:
            ref = self.picking_id.name

        if not self._is_in() and not self._is_out():
            valuation_amount = self._get_price_unit() * qty     
	    #valuation_amount = self._get_price_unit()
        
        debit_value = self.company_id.currency_id.round(valuation_amount)

        # check that all data is correct
        if self.company_id.currency_id.is_zero(debit_value):
            raise UserError(_("The cost of %s is currently equal to 0. Change the cost or the configuration of your product to avoid an incorrect valuation.") % (self.product_id.name,))
        credit_value = debit_value
        if self.location_id.usage == 'internal':
            qty = qty * -1
            debit_value = debit_value * -1
            credit_value = debit_value
        else: 
            qty = qty
            debit_value = self.company_id.currency_id.round(valuation_amount)
            credit_value = debit_value
        partner_id = (self.picking_id.partner_id and self.env['res.partner']._find_accounting_partner(self.picking_id.partner_id).id) or False
        debit_line_vals = {
            'name': self.name,
            'product_id': self.product_id.id,
            'quantity': qty,
            'product_uom_id': self.product_id.uom_id.id,
            'ref': ref,
            'partner_id': partner_id,
            'debit': debit_value if debit_value > 0 else 0,
            'credit': -debit_value if debit_value < 0 else 0,
            'account_id': debit_account_id,
        }
        credit_line_vals = {
            'name': self.name,
            'product_id': self.product_id.id,
            'quantity': qty,
            'product_uom_id': self.product_id.uom_id.id,
            'ref': ref,
            'partner_id': partner_id,
            'credit': credit_value if credit_value > 0 else 0,
            'debit': -credit_value if credit_value < 0 else 0,
            'account_id': credit_account_id,
        }
        res = [(0, 0, debit_line_vals), (0, 0, credit_line_vals)]
        if credit_value != debit_value:
            # for supplier returns of product in average costing method, in anglo saxon mode
            diff_amount = debit_value - credit_value
            price_diff_account = self.product_id.property_account_creditor_price_difference
            if not price_diff_account:
                price_diff_account = self.product_id.categ_id.property_account_creditor_price_difference_categ
            if not price_diff_account:
                raise UserError(_('Configuration error. Please configure the price difference account on the product or its category to process this operation.'))
            price_diff_line = {
                'name': self.name,
                'product_id': self.product_id.id,
                'quantity': qty,
                'product_uom_id': self.product_id.uom_id.id,
                'ref': ref,
                'partner_id': partner_id,
                'credit': diff_amount > 0 and diff_amount or 0,
                'debit': diff_amount < 0 and -diff_amount or 0,
                'account_id': price_diff_account.id,
            }
            res.append((0, 0, price_diff_line))

        res[0][2]['stock_move_id'] = self.id
        res[1][2]['stock_move_id'] = self.id

        return res    
    

class account_move(models.Model):
    _inherit = "account.move"

    @api.model
    def show_stock_moves(self):
        res = []
        self._cr.execute(
                '''SELECT distinct stock_move_id
                   FROM account_move_line
                   WHERE move_id = %s;''' % (self.id))
        res = filter(None, map(lambda x:x[0], self._cr.fetchall()))
        return {
                'domain': "[('id','in',[" + ','.join(map(str, list(res))) + "])]",
                'name'      : _('Related Stock Moves'),
                'view_mode': 'tree,form',
                'view_type': 'form',
                'context': {'tree_view_ref': 'stock.view_move_tree'},
                'res_model': 'stock.move',
                'type': 'ir.actions.act_window',
            }


"""class stock_quant(osv.osv):
    _inherit = "stock.quant"
    
    if release.major_version == "9.0":    
        def _prepare_account_move_line(self, cr, uid, move, qty, cost, credit_account_id, debit_account_id, context=None):
            res = super(stock_quant, self)._prepare_account_move_line(cr, uid, move, qty, cost, credit_account_id, debit_account_id, context)
            if res: # Para el caso de una Recepcion de Proveedor con cantidad mayor a la solicitada y sin precio promedio previo.
                res[0][2]['stock_move_id'] = move.id
                res[1][2]['stock_move_id'] = move.id
            return res"""


class stock_picking(models.Model):
    _inherit = "stock.picking"
    
    @api.model
    def show_entry_lines(self):
        res = []
        for picking in self:
            move_ids = [move.id for move in picking.move_lines]
        move_line_ids = self.env['account.move.line'].search([('stock_move_id','in',move_ids)])
        res = [x.id for x in move_line_ids]
        if not res:
            raise UserError(_('Aviso !\nNo hay partidas contables relacionadas a este movimiento'))
        return {
                'domain': "[('id','in',[" + ','.join(map(str, list(res))) + "])]",
                'name'      : _('Related Journal Entries'),
                'view_mode': 'tree,form',
                'view_type': 'form',                
                'res_model': 'account.move.line',
                'type': 'ir.actions.act_window',
            }

    @api.model
    def show_journal_entries(self):
        res = []
        for picking in self:
            move_ids = [move.id for move in picking.move_lines]
        move_line_ids = self.env['account.move.line'].search([('stock_move_id','in',move_ids)])
        res = [x.move_id.id for x in move_line_ids]
        if not res:
            raise UserError(_('Aviso !\nNo hay partidas contables relacionadas a este movimiento'))
        return {
                'domain': "[('id','in',[" + ','.join(map(str, list(res))) + "])]",
                'name'      : _('Related Account Moves'),
                'view_mode': 'tree,form',
                'view_type': 'form',                
                'res_model': 'account.move',
                'type': 'ir.actions.act_window',
            }


