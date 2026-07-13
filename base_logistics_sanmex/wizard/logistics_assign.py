# -*- coding: utf-8 -*-
import logging

from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError

_logger = logging.getLogger(__name__)


class LogisticsAssign(models.TransientModel):
    _name = 'logistics.assign'
    _description = _('Asignacion de logistica')

    name = fields.Char(_('Name'))
    route_id = fields.Many2one('logistics.route', string='Ruta')
    stock_house_id = fields.Many2one('stock.warehouse', string='Almacén')
    sale_id = fields.Many2one('sale.order', string='Orden de venta', required=True, ondelete='cascade')
    partner_id = fields.Many2one('res.partner', string='Cliente')
    user_id = fields.Many2one('res.users', string='Operador')
    date_delivery = fields.Datetime('Fecha de entrega')
    logistics_assign_line_ids = fields.One2many('logistics.assign.line', 'logistics_assign_id', string="Líneas")

    @api.onchange('sale_id')
    def _get_wizard_lines(self):
        """Use Wizard lines to set by default the pickup/return value
        to the total pickup/return value expected"""
        rental_lines_ids = self.env.context.get('order_line_ids', [])
        rental_lines_to_process = self.env['sale.order.line'].browse(rental_lines_ids)

        # generate line values
        if rental_lines_to_process:
            lines_values = []
            for line in rental_lines_to_process:
                lines_values.append(self.env['logistics.assign.line']._default_wizard_line_vals(line))

            self.logistics_assign_line_ids = [(6, 0, [])] + [(0, 0, vals) for vals in lines_values]

    def add(self):
        LogisticsAssign =  self.env["logistics.planning"]
        LogisticsAssign.create({
            'name': self.sale_id.name,
            'route_id': self.route_id.id,
            'stock_house_id': self.stock_house_id.id,
            'sale_id': self.sale_id.id,
            'partner_id': self.partner_id.id,
            'user_id': self.user_id.id,
            'date_delivery': self.date_delivery,
        })

        ##ADD NOTIFICATION USER
        message ="Esto es una prueba de notificacion"
        notification = {
                'type': 'success',
                'message': message,
                'sticky': True,
        }
        self.env["bus.bus"]._sendone(
            self.env["res.partner"].browse(self.stock_house_id.user_id.partner_id.id),
            'simple_notification',
            notification
        )

        _logger.info('Hello Wizard')
        return True

class LogisticsAssignLine(models.TransientModel):
    _name = 'logistics.assign.line'


    @api.model
    def _default_wizard_line_vals(self, line):
        delay_price = line.product_id._compute_delay_price(fields.Datetime.now() - line.return_date)
        return {
            'order_line_id': line.id,
            'product_id': line.product_id.id,
            'qty_reserved': line.product_uom_qty,
        }

    logistics_assign_id = fields.Many2one('logistics.assign', 'Asignacion Logistica Wizard', required=True, ondelete='cascade')

    order_line_id = fields.Many2one('sale.order.line', required=True, ondelete='cascade')
    product_id = fields.Many2one('product.product', string='Producto', required=True, ondelete='cascade')
    qty_reserved = fields.Float("Reservado")