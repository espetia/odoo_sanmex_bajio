# -*- coding: utf-8 -*-
##############################################################################
#                 @author JORGE CHUC
#
##############################################################################

{
    'name': 'Modifica el diseño de la factura',
    'version': '15.24',
    'description': ''' Diseño de facturas sanmex
    ''',
    'category': 'Accounting',
    'author': 'Jorge Chuc',
    'website': '',
    'depends': [
        'sale','account','purchase', 'base_vat','cdfi_invoice',
    ],
    'data': [
        'report/report_cdfi_invoice_sanmex.xml'
    ],
    #'images': ['static/description/banner.jpg'],
    'application': False,
    'installable': True,
    #'price': 0.00,
    #'currency': 'USD',
    'license': 'OPL-1',
}