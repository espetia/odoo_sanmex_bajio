# -*- coding: utf-8 -*-
{
    'name': 'San Mex Invoice Layout',
    'version': '15.0.1.0.0',
    'category': 'Accounting',
    'summary': 'Custom Invoice QWeb Report for San Mex',
    'description': 'Replaces the default account.report_invoice_document with a custom layout, overriding cdfi_invoice.',
    'author': 'San Mex',
    'depends': ['account', 'cdfi_invoice'],
    'data': [
        'data/report_paperformat.xml',
        'views/account_journal_views.xml',
        'views/report_invoice_sanmex.xml',
    ],
    'installable': True,
    'application': False,
    'auto_install': False,
    'license': 'LGPL-3',
}
