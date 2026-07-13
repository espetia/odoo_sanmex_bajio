# -*- encoding: utf-8 -*-
from odoo.exceptions import UserError, ValidationError
from odoo import api, fields, models, _
import odoo.addons.decimal_precision as dp
from odoo.osv import osv

class account_move_line(models.Model):
    _inherit = "account.move.line"

    stock_move_id   = fields.Many2one('stock.move', 'Stock Move', readony=True)
    location_id     = fields.Many2one('stock.location', related='stock_move_id.location_id', string='Source Location',
                                        store=True, help='Location Move Source')
    location_dest_id= fields.Many2one('stock.location', related='stock_move_id.location_dest_id',
                                        string='Destination Location',  store=True,
                                        help="Location Move Destination")

class stock_move(models.Model):
    _inherit = "stock.move"

    @api.model
    @api.depends('state', 'product_uom_qty','price_unit')
    def _calc_amount_stock_move(self):
        context = dict(self._context or {})        
        for move in self:
            sign = 0.0
            if move.state != 'cancel':
                if move.location_id.usage in ('customer','supplier','inventory', 'production','transit') and \
                    move.location_dest_id.usage =='internal':
                    sign = 1.0
                elif move.location_id.usage =='internal' and \
                    move.location_dest_id.usage in ('customer','supplier','inventory', 'production','transit'):
                    sign = -1.0
            move.amount_stock_move = (move.product_uom_qty * move.price_unit or 0.0) * sign
    
    account_move_line_ids = fields.One2many('account.move.line', 'stock_move_id', string='Partidas Contables', readonly=True)
    amount_stock_move     = fields.Float(compute='_calc_amount_stock_move', string='Stock Move Value', 
                                              digits=dp.get_precision('Product Price'), store=True, readonly=True)
    




