# -*- coding: utf-8 -*-
import logging

from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError

_logger = logging.getLogger(__name__)


class SaleOrder(models.Model):
    _inherit = 'sale.order'

    state_sanmex_logistics = fields.Selection(
        string=_('Estatus Sanmex'),
        selection=[
            ('to_delivery', 'Para entregar'),
            ('to_return', 'Para Retiro'),
        ],
    )

    def action_call_logistics_assign(self):
        view = self.env.ref('base_logistics_sanmex.view_logistics_assign_form')
        lines_to_order = self.order_line.filtered(
            lambda r: r.state in ['sale', 'done'] and r.is_rental)
        return {
            'name': _(' Logistica Asignación'),
            'type': 'ir.actions.act_window',
            'view_type': 'form',
            'view_mode': 'form',
            'target': 'new',
            'view_id': view.id,
            'views': [(view.id, 'form')],
            'res_model': 'logistics.assign',
            'context': {'default_name': self.name,
                        'default_sale_id':self.id,
                        'default_partner_id': self.partner_id.id,
                        'default_stock_house_id': self.warehouse_id.id,
                        'order_line_ids': lines_to_order.ids}
        }
    
    @api.model
    def retrieve_rent_dashboard(self):
        result = {
            'to_delivery': 0,
            'to_return': 0,
            'sanitary_qty_dis': 0,
        }

        so =  self.env["sale.order"]
        result['to_delivery'] = so.search_count([('state_sanmex_logistics','=','to_delivery')])
        result['to_return'] = so.search_count([('state_sanmex_logistics','=','to_return')])

        slot = self.env["stock.production.lot"]
        result['sanitary_qty_dis'] = slot.search_count([('is_lot_sanmex', '=',True),('stage_product_id','=',1)])

        return result
    
    def popupNofication(self):
        message ="Esto es una prueba de notificacion"
        notification = {
                'type': 'success',
                'message': message,
                'sticky': True,
        }
        self.env["bus.bus"]._sendone(
            self.env["res.partner"].browse(6),
            'simple_notification',
            notification
        )

        return True
    
    def action_confirm(self):
        res = super(SaleOrder, self).action_confirm()
        ##ADD NOTIFICATION USER
        if self.is_rental_order:
            message ="Orden de alquiler confirmada"
            notification = {
                    'type': 'success',
                    'message': message,
                    'sticky': True,
            }
            self.env["bus.bus"]._sendone(
                self.env["res.partner"].browse(self.warehouse_id.user_id.partner_id.id),
                'simple_notification',
                notification
            )
        return res