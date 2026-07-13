# -*- encoding: utf-8 -*-

{
    "name": "MX - Account Tax Cash Basis", 
    "version": "1.0", 
    "author": "Qx Unit de México", 
    "category": "Impuestos", 
    "description": """

The tax actually paid/cashed in the move of payment,
====================================================


    """, 
    "website": "http://www.qxunit.com.mx", 
    #"license": "AGPL-3", 
    "depends": [
        "account", 
        "account_invoice_payment_by_date_due", 
        "account_move_line_base_tax",  

    ], 
    "demo": [], 
    "data": ["account_tax_view.xml",
              "security/ir.model.access.csv"], 
    "js": [], 
    "css": [], 
    "qweb": [], 
    "installable": True, 
    "auto_install": False, 
    "active": False
}
