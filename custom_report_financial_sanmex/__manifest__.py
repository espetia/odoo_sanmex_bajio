# -*- coding: utf-8 -*-
{
    'name': 'Custom_report_financial_sanmex',
    'version': '',
    'description': """ Custom_report_financial_sanmex Description """,
    'summary': """ Custom_report_financial_sanmex Summary """,
    'author': '',
    'website': '',
    'category': '',
    'depends': ['base', 'account'],
    'data': [
        'report/account_invoice_due_report_view.xml',
        'security/ir.model.access.csv',
        'views/account_due_report_menu.xml',
        'security/report_security.xml',
    ],
    'application': True,
    'installable': True,
    'auto_install': False,
    'license': 'LGPL-3',
}
