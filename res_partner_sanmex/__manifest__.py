# -*- coding: utf-8 -*-
{
    'name': 'Customizacion proveedores o clientes',
    'version': '',
    'summary': """ Se agregan campos internos para el uso de nombre comercial en el apartado de compras """,
    'author': '',
    'website': '',
    'category': '',
    'depends': ['base', 'base_vat','purchase','purchase_custom'],
    "data": [
        "views/res_partner_views.xml",
        "views/purchase_order_views.xml"
    ],
    'installable': True,
    'auto_install': False,
    'license': 'LGPL-3',
}
