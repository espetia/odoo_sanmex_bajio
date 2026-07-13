# -*- coding: utf-8 -*-
##############################################################################
#                 @author JORGE CHUC
#
##############################################################################

{
    'name': 'Cargar información de facturas desde el Xml desde los attachments de la factura',
    'version': '15.24',
    'description': ''' Factura Electronica módulo de ventas para Mexico
    ''',
    'category': 'Accounting',
    'author': 'Jorge Chuc',
    'website': '',
    'depends': [
        'sale','account','purchase', 'base_vat','cdfi_invoice',
    ],
    'data': [
        'views/cfdi_view_attachment_get.xml',
    ],
    #'images': ['static/description/banner.jpg'],
    'application': False,
    'installable': True,
    #'price': 0.00,
    #'currency': 'USD',
    'license': 'OPL-1',
}