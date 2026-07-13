# -*- encoding: utf-8 -*-
##############################################################################

{
    'name': 'Acount Invoice Cancel without removing Account Move',
    'version': '1',
    "author" : "Qx Unit de México",
    "category" : "Account",
    'description': """
Cancelación de factura
===================================================



    """,
    "website" : "http://www.qxunit.com.mx",
    "license" : "AGPL-3",
    "depends" : ["account", "base"],
    "data" : ['account_view.xml',
              'account_invoice_view.xml',
              
              #'catalogocan_view.xml'
                    ],
    "installable" : True,
    "active" : False,
}
