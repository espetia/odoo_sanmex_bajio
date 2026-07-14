# -*- coding: utf-8 -*-
{
    "name": "Purchase_report_sanmex",
    "version": "",
    "summary": """ Purchase_report_sanmex Summary """,
    "author": "",
    "website": "",
    "category": "",
    "depends": ["base", "purchase", "web", "purchase_stock", "res_partner_sanmex", "purchase_order_payment_status"],
    "data": [
        "report/purchase_report_smx.xml",
        "report/purchase_report_sanmex_views.xml",
        "security/ir.model.access.csv",
        "security/report_security.xml",
    ],
    "application": False,
    "installable": True,
    "auto_install": False,
    "license": "LGPL-3",
}
