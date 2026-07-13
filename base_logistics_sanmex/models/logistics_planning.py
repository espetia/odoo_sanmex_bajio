# -*- coding: utf-8 -*-
import logging

from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError

_logger = logging.getLogger(__name__)


class LogisticsPlanning(models.Model):
    _name = 'logistics.planning'
    _description = _('Logistica Planeacion')

    name = fields.Char('Nombre')
    route_id = fields.Many2one('logistics.route', string='Ruta')
    stock_house_id = fields.Many2one('stock.warehouse', string='Almacén')
    product_tmplt_id = fields.Many2one('product.template', string='Producto Temp')
    product_id = fields.Many2one('product.product', string='Producto')
    partner_id = fields.Many2one('res.partner', string='Cliente')
    sale_id = fields.Many2one('sale.order', string='Orden de venta')
    date_rent = fields.Date('Fecha de renta')
    date_order = fields.Datetime(related='sale_id.date_order', string="Fecha de la orden")
    date_delivery = fields.Datetime('Fecha de entrega')
    date_return = fields.Datetime('Fecha prevista de devolución')
    qty_demand = fields.Integer('Cantidad pedida')
    qty_confirm = fields.Integer('Cantidad entregada')
    type_product = fields.Selection(
        string=_('Tipo de producto'),
        selection=[
            ('obra', 'Sanitario de obra'),
            ('evento', 'Sanitario de evento'),
        ],
    )
    #employee_id = fields.Many2one('hr.employee', string='Operador')
    user_id = fields.Many2one('res.users', string='Operador')

    state = fields.Selection(
        string=_('Estado'),
        selection=[
            ('draft', 'Borrador'),
            ('confirm', 'Confirmado'),
            ('in_progress', 'Por entregar'),
            ('delivery', 'Entregado'),
        ],
        default="confirm",
    )

    def action_assign_serial(self):
        #open wizard
        view = self.env.ref('base_logistics_sanmex.wizard_view_sanmex_assign_rent_lot_form')
        return {
            'name': _(' Asignar Serie'),
            'type': 'ir.actions.act_window',
            'view_type': 'form',
            'view_mode': 'form',
            'target': 'new',
            'view_id': view.id,
            'views': [(view.id, 'form')],
            'res_model': 'sanmex.assign.rent.lot',
            'context': {'default_name': self.name,
                        'default_sale_id':self.id,
                        'default_partner_id': self.partner_id.id,
                        'default_stock_house_id': self.stock_house_id.id,
                        'default_route_id': self.route_id.id,
                        'default_user_id': self.user_id.id,
                        }
        }
        self.ensure_one()
        if self.state == 'confirm':
            pass

    @api.model
    def retrieve_planning_dashboard(self):
        vals = {
            'total_confirm': 0,
            'total_in_progress': 0,
            'total_delivery': 0,
            'sanitary_qty_dis': 0,
            'sanitary_qty_clean':0,
            'sanitary_qty_mantt':0,
            }
        logistics_m = self.env['logistics.planning']
        vals['total_confirm'] = logistics_m.search_count([('state','=','confirm')])
        vals['total_in_progress'] = logistics_m.search_count([('state','=','in_progress')])
        vals['total_delivery'] = logistics_m.search_count([('state','=','delivery')])
        

        slot = self.env["stock.production.lot"]
        vals['sanitary_qty_dis'] = slot.search_count([('is_lot_sanmex', '=',True),('stage_product_id','=',1)])
        vals['sanitary_qty_clean'] = slot.search_count([('is_lot_sanmex', '=',True),('stage_product_id','=',3)])
        vals['sanitary_qty_mantt'] = slot.search_count([('is_lot_sanmex', '=',True),('stage_product_id','=',2)])

        return vals
        pass

    @api.model
    def barcode_search(self, args):
        pass

    def action_print_report_planning(self):
        return self.env.ref('base_logistics_sanmex.report_action_logistic_planning_out_sanmex_view').report_action(self)
        pass