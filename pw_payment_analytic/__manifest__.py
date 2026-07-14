# -*- coding: utf-8 -*-
{
    'name': 'Payment Analytic Account and Tags',
    'category': 'Accounting',
    'summary': 'This module help you to set analytic account on payment and journal entries | Analytic Account on Customer Payment | Analytic Account on Vendor Payment | Payment analytic account and analytic tag | Payment voucher with analytic account & analytic tag',
    'description': """
This apps helps you to set analytic account on payment and journal entries.
""",
    'author': 'Preway IT Solutions',
    'version': '1.0',
    'depends': ['account'],
    "data": [
        'security/account_security.xml',
        # 'views/account_payment_view.xml',
        'wizard/account_payment_register.xml',
    ],
    'price': 20.0,
    'currency': 'EUR',
    'installable': True,
    'auto_install': False,
    "images":["static/description/Banner.png"],
}
