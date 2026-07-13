# -*- encoding: utf-8 -*-
#
{
    "name": "Amount Base Account Move Line", 
    "version": "1.0", 
    "author": "Qx Unit de México", 
    "category": "Generic Modules", 
    "description": """
    This module adds fields:
        - amount_base
        - tax_id_secondary
    in account_move_line. These fields are filled when you validate the invoice.
    """, 
    "website": "http://www.qxunit.com.mx/", 
    "depends": [
        "account",  
        "sat_catalogos"
    ], 
    "demo": [], 
    "data": [
        "account_view.xml"
    ], 
    "test": [], 
    "js": [], 
    "css": [], 
    "qweb": [], 
    "installable": True, 
    "auto_install": False, 
    "active": False
}