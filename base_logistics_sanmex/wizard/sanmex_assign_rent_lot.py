# -*- coding: utf-8 -*-
import logging

from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError

_logger = logging.getLogger(__name__)


class SanmexAssignRentLot(models.TransientModel):
    _name = 'sanmex.assign.rent.lot'
    _inherit = "barcodes.barcode_events_mixin"
    _description = _('Asignar Serie a rentar')
    # To prevent remove the record wizard until 2 days old
    _transient_max_hours = 48
    _allowed_product_types = ["product", "consu"]

    barcode = fields.Char()
    name = fields.Char(_('Nombre'))
    route_id = fields.Many2one('logistics.route', string='Ruta')
    stock_house_id = fields.Many2one('stock.warehouse', string='Almacén')
    sale_id = fields.Many2one('sale.order', string='Orden de venta', required=True, ondelete='cascade')
    partner_id = fields.Many2one('res.partner', string='Cliente')
    user_id = fields.Many2one('res.users', string='Operador')
    assign_line_rent_ids = fields.One2many('assign.rent.line.lot', 'assign_rent_id', string="Líneas")
    

    def add(self):
        _logger.info('Hello Wizard')

    @api.model
    def barcode_search(self, args):
        self.barcode = args[0]
        #return {'type': 'ir.actions.act_window_close'}
        return True
    def print_report(self):
        pass
        #return self.env.ref('sanmex.action_report_assign_rent_lot').report_action(self)

    
    @api.onchange('barcode')
    def _onchange_barcode(self):
        search_barcode = self.barcode
        stock_product = self.env['stock.production.lot'].search([('name', '=', search_barcode )])
        if stock_product:
            self.name = stock_product.name
            #raise UserError(_("Lote detectado"+str(stock_product.id)))
            self.assign_line_rent_ids.create(
                {
                    'lot_id': stock_product.id,
                    'assign_rent_id': self.id,
                    'lot_qty': stock_product.product_qty
                }
            )
            
            #raise UserError(_("Lote detectado"))
        
    class AssignRentLineLot(models.TransientModel):
        _name = 'assign.rent.line.lot'

        assign_rent_id = fields.Many2one('sanmex.assign.rent.lot', 'Asignacion Rental Wizard', required=True, ondelete='cascade')
        lot_id = fields.Many2one('stock.production.lot', string='Lote')
        lot_name = fields.Char('Lote', related='lot_id.name')
        lot_qty = fields.Integer('Cantidad')