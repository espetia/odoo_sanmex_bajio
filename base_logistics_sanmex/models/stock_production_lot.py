# -*- coding: utf-8 -*-
import logging

from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError

_logger = logging.getLogger(__name__)


class StockProductionLot(models.Model):
    _inherit = 'stock.production.lot'

    is_lot_sanmex = fields.Boolean('Lote Sanmex')
    type_product = fields.Selection(
        string=_('Tipo de producto'),
        selection=[
            ('obra', 'Sanitario de obra'),
            ('evento', 'Sanitario de evento'),
        ],
    )
    color_product = fields.Selection(
        string=_('Color'),
        selection=[
            ('rojo', 'Rojo'),
            ('blanco', 'Blanco'),
            ('azul','Azul'),
        ],
    )
    model_product = fields.Selection(
        string=_('Modelo'),
        selection=[
            ('1', 'JJ'),
            ('2', 'Flus'),
            ('3', 'Lujo'),
        ],
    )
    state_inventory_product = fields.Selection(
        string=_('Estado de ubicación'),
        selection=[
            ('available', 'Disponible'),
            ('maintenance', 'Mantenimiento'),
            ('cleaning','Limpieza'),
            ('damaged','Dañado'),
            ('rented','Rentado')
        ],
    )
    stage_product_id = fields.Many2one('stock.stage.product', string='Etapas de Bodega', group_expand='_read_group_stage_product_ids')
    kanban_state = fields.Selection([('normal', 'Sin iniciar'),('done', 'En progreso'),('blocked', 'Bloqueado')], string='Kanban State', copy=False, default='normal', required=True)
    stock_house_id = fields.Many2one('stock.warehouse', string="Almacén", related="product_id.stock_house_id",readonly=True, store=True)
    color = fields.Integer('Color')

    @api.model
    def _read_group_stage_product_ids(self, stages, domain, order):
        return self.env['stock.stage.product'].search([], order=order)

    @api.model
    def barcode_search(self, args):
        product = self.env['product.product'].search([('barcode', '=', args[0])])
        #return {'type': 'ir.actions.act_window_close'}
        return True
    
    @api.model
    def retrieve_stock_lot_dashboard(self):
        vals = {
            'sanitary_qty_dis':0,
            'sanitary_qty_clean':0,
            'sanitary_qty_mantt':0,
            'total_confirm': 0,
            'total_in_progress': 0,
            'total_delivery': 0,
            }
        logistics_m = self.env['logistics.planning']
        vals['total_confirm'] = logistics_m.search_count([('state','=','confirm')])
        vals['total_in_progress'] = logistics_m.search_count([('state','=','in_progress')])
        vals['total_delivery'] = logistics_m.search_count([('state','=','delivery')])

        slot = self.env["stock.production.lot"]
        vals['total_qty_product'] = slot.search_count([('is_lot_sanmex', '=',True)])
        vals['sanitary_qty_stock'] = slot.search_count([('is_lot_sanmex', '=',True),('stage_product_id','=',6)])
        vals['sanitary_qty_dis'] = slot.search_count([('is_lot_sanmex', '=',True),('stage_product_id','=',1)])
        vals['sanitary_qty_clean'] = slot.search_count([('is_lot_sanmex', '=',True),('stage_product_id','=',3)])
        vals['sanitary_qty_mantt'] = slot.search_count([('is_lot_sanmex', '=',True),('stage_product_id','=',2)])

        return vals
        pass