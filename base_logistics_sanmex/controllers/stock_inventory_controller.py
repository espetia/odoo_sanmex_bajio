from odoo import http
from odoo.http import request


class StockSanitary(http.Controller):
    
    """ 
        Routes:
            /get_panel_data_stock_sanmex: url description
    """
    
    @http.route('/logistics/get_panel_data_stock_sanmex', type='json', auth='user')
    def get_panel_data_stock_sanmex(self):
        vals = {
            'total_confirm': 0,
            'total_in_progress': 0,
            'total_delivery': 0,
            'sanitary_qty_dis': 0,
            'sanitary_qty_clean':0,
            'sanitary_qty_mantt':0,
            }
        logistics_m = request.env['logistics.planning']
        vals['total_confirm'] = logistics_m.search_count([('state','=','confirm')])
        vals['total_in_progress'] = logistics_m.search_count([('state','=','in_progress')])
        vals['total_delivery'] = logistics_m.search_count([('state','=','delivery')])
        

        slot = request.env["stock.production.lot"]
        vals['sanitary_qty_dis'] = slot.search_count([('is_lot_sanmex', '=',True),('stage_product_id','=',1)])
        vals['sanitary_qty_clean'] = slot.search_count([('is_lot_sanmex', '=',True),('stage_product_id','=',3)])
        vals['sanitary_qty_mantt'] = slot.search_count([('is_lot_sanmex', '=',True),('stage_product_id','=',2)])
        
        return {
            'html': request.env.ref('base_logistics_sanmex.panel_stock_sanmex')._render({
                'object': request.env['logistics.planning'],
                'values' : vals
            })
        }
    