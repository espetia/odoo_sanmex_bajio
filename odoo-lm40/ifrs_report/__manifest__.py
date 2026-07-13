# -*- coding: utf-8 -*-

{
    "name": "IFRS",
    "version": "1.0",
    "author" : "Argil",
    "category": "Accounting & Finance",
    "website": "http://www.argil.mx",
    "license": "",
    "depends": [
        
        "account",
        
        "Plan_contable",
        "account_period_and_fiscalyear",
    ],
    "demo": [],
    "data": [
        "security/security.xml",
        "security/ir.model.access.csv",
        "view/wizard.xml",
        "view/ifrs_view.xml",        
        "report/template.xml",        
        "view/report.xml",
        "data/data_ifrs.xml",
    ],
    "test": [],
    "js": [],
    "css": [],
    "qweb": [],
    "installable": True,
    "auto_install": False,
    "application": True,
}
