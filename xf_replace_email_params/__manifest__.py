# -*- coding: utf-8 -*-

{
    'name': 'Replace email_from and reply_to',
    'version': '1.1.3',
    'category': 'Productivity,Discuss,Extra Tools',
    'summary': """
    Replace "Email From" and "Reply To" parameters in emails
    | replace email from
    | replace reply to
    | substitute email_from
    | substitute reply_to
    | overwrite email_from
    | overwrite reply_to
    | custom email_from
    | custom reply_to
    | replace email sender
    | replace sender
    | overwrite sender
    """,
    'author': 'XFanis',
    'support': 'xfanis.dev@gmail.com',
    'website': 'https://xfanis.dev/odoo.html',
    'license': 'OPL-1',
    'price': 15,
    'currency': 'EUR',
    'description': """
    This module helps to replace/overwrite email_from and reply_to parameters of outgoing emails and notifications.
    After module installation you can customize email from and reply to options.
    """,
    'depends': ['mail'],
    'data': [
        'security/ir.model.access.csv',
        'views/mail_replace_rule.xml',
    ],
    'images': [
        'static/description/xf_replace_email_params.png',
    ],
    'demo': [],
    'installable': True,
    'application': True,
    'qweb': [],
}
