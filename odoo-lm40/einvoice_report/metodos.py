# -*- coding: utf-8 -*-
from odoo import api, models, release

class SaleOrder(models.Model):
    _inherit = "sale.order"

    
    def init(self):
        cr = self._cr        
        cr.execute("""update ir_ui_view set active=False where name='report_invoice_document_inherit_sale_stock';""")
        cr.execute("""update ir_ui_view set active=False where name='stock_account_report_invoice_document';""")
        cr.execute("""update ir_ui_view set active=False where name='report_invoice_document_inherit_sale';""")
        cr.execute("""update ir_ui_view set active=False where name='report_invoice_document_mx';""")
        


        

            
            
