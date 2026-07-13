# -*- coding: utf-8 -*-
###############################################################################
#
#	Copyright (c) All rights reserved:
#		(c) 2024  production_lot_controller.py
#
#	This program is free software: you can redistribute it and/or modify
#	it under the terms of the GNU Affero General Public License as
#	published by the Free Software Foundation, either version 3 of the
#	License, or (at your option) any later version.
#
#	This program is distributed in the hope that it will be useful,
#	but WITHOUT ANY WARRANTY; without even the implied warranty of
#	MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
#	GNU Affero General Public License for more details.
#
#	You should have received a copy of the GNU Affero General Public License
#	along with this program.  If not, see http://www.gnu.org/licenses
#	
#	Odoo and OpenERP is trademark of Odoo S.A.
#
###############################################################################
from odoo import http
from odoo.http import request


class ProductionLot(http.Controller):
    
    """ 
        Routes:
            /get_panel_data_production_lot_sanmex: url description
    """
    
    @http.route('/logistics/get_panel_data_production_lot_sanmex', type='json', auth='user')
    def get_panel_data_production_lot_sanmex(self):
        vals = {
            'sanitary_qty_dis':0,
            'sanitary_qty_clean':0,
            'sanitary_qty_mantt':0,
            'total_confirm': 0,
            'total_in_progress': 0,
            'total_delivery': 0,
            }
        logistics_m = request.env['logistics.planning']
        vals['total_confirm'] = logistics_m.search_count([('state','=','confirm')])
        vals['total_in_progress'] = logistics_m.search_count([('state','=','in_progress')])
        vals['total_delivery'] = logistics_m.search_count([('state','=','delivery')])

        slot = request.env["stock.production.lot"]
        vals['total_qty_product'] = slot.search_count([('is_lot_sanmex', '=',True)])
        vals['sanitary_qty_stock'] = slot.search_count([('is_lot_sanmex', '=',True),('stage_product_id','=',6)])
        vals['sanitary_qty_dis'] = slot.search_count([('is_lot_sanmex', '=',True),('stage_product_id','=',1)])
        vals['sanitary_qty_clean'] = slot.search_count([('is_lot_sanmex', '=',True),('stage_product_id','=',3)])
        vals['sanitary_qty_mantt'] = slot.search_count([('is_lot_sanmex', '=',True),('stage_product_id','=',2)])

        return {
            'html': request.env.ref('base_logistics_sanmex.panel_lot_sanmex')._render({
                'object': request.env['stock.production.lot'],
                'values' : vals
            })
        }