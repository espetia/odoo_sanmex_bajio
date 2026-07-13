# -*- coding: utf-8 -*-
import logging

from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError

_logger = logging.getLogger(__name__)


class WizardStockLotState(models.TransientModel):
    _name = 'wizard.stock.lot.state'
    _description = _('Mover Sanitarios')

    name = fields.Char(_('Name'))
    stock_house_id = fields.Many2one('stock.warehouse', string='Almacén')
    barcode = fields.Char()
    lot_id = fields.Many2one('stock.production.lot', string='Lote')
    stage_product_id_actually = fields.Many2one('stock.stage.product', string='Etapa Actual')
    stage_product_id_destination = fields.Many2one('stock.stage.product', domain="[('id', '!=', stage_product_id_actually)]", string='Etapa Destino')

    def add(self):
        for lot_sanitary in self.lot_id:
            lot_sanitary.write({
                'stage_product_id': self.stage_product_id_destination.id
            })
            #if lot_sanitary.stage_product_id_actually.id == self.stage_product_id_destination.id:
        #_logger.info('Hello Wizard')
        return {'type': 'ir.actions.client','tag':'reload'}

    @api.onchange('lot_id')
    def _onchange_lot_id(self):
        if self.lot_id:
            self.stage_product_id_actually = self.lot_id.stage_product_id
    

    @api.onchange('barcode')
    def _onchange_barcode(self):
        search_barcode = self.barcode
        stock_product = self.env['stock.production.lot'].search([('name', '=', search_barcode )])
        if stock_product:
            self.lot_id = stock_product.id
            self.stage_product_id_actually = stock_product.stage_product_id.id
                #raise UserError(_("Lote detectado"+str(stock_product.id)))
                #self.assign_line_rent_ids.create(
                #    {
                #        'lot_id': stock_product.id,
                #        'assign_rent_id': self.id,
                #        'lot_qty': stock_product.product_qty
                #    }
                #)