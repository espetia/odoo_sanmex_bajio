# -*- coding: utf-8 -*-
{
    'name': 'San Mex Company Custom',
    'version': '15.0.1.0.0',
    'summary': 'Customizations for San Mex Company',
    'description': """
        This module includes customizations for the purchase module.
    """,
    'author': 'Carlos Espetia',
    'website': 'carlosespetia.com',
    'category': 'Uncategorized',
    'depends': ['purchase', 'purchase_stock', 'purchase_custom', 'pw_payment_analytic', 'sale', 'account', 'cdfi_invoice','res_partner_sanmex'],
    'data': [
        'data/mail_template_ppd_missing.xml',
        'data/ir_cron_ppd_missing.xml',
        'views/purchase_order_view.xml',
        'views/res_config_settings_views.xml',
        'report/purchase_order_view.xml',
        'security/ir.model.access.csv',
        'views/purchase_payable_report_view.xml',
        'views/account_move_debtors_view.xml',
        'views/customer_status_view.xml',
    ],
    'assets': {
        'web.assets_backend': [
            'san_mex_company_custom/static/src/js/customer_status_dashboard.js',
        ],
        'web.assets_qweb': [
            'san_mex_company_custom/static/src/xml/customer_status_dashboard.xml',
        ],
    },
    'post_init_hook': 'post_init_hook',
    'installable': True,
    'application': False,
    'auto_install': False,
    'license': 'LGPL-3',
}
