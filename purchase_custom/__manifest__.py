# -*- coding: utf-8 -*-
{
    'name': "Personalizaciones Compras",

    'summary': """
        Personalizaciones al modulo de compras y contabilidad para SANMEX Qroo""",

    'description': """
        Long description of module's purpose
    """,

    'author': "FTNMX",
    'website': "http://www.formalizatunegocio.com",

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/15.0/odoo/addons/base/data/ir_module_category_data.xml
    # for the full list
    'category': 'Uncategorized',
    'version': '0.1',

    # any module necessary for this one to work correctly
    'depends': ['base', 'purchase', 'base_account_budget', 'account_fleet'],

    # always loaded
    'data': [
        # 'security/ir.model.access.csv',
        'views/views.xml',
        'views/templates.xml',
    ],
    # only loaded in demonstration mode
    'demo': [
        'demo/demo.xml',
    ],
}
