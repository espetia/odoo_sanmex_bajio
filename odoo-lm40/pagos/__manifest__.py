# -*- encoding: utf-8 -*-

{
    "name"      : "Complemento Recepcion de Pagos",
    "version"   : "1.0",   
    "author"    : "Qx Unit de México",
    "category"  : "pagos",
    "description" : """
Complemento Recepcion de Pagos
===================================================

    Este módulo le permite emitir el CFDI con el Complemento de recepción de pagos
    

    """,
    "website" : "http://www.qxunit.com.mx",
    "depends" : [
                 "sat_catalogos",
                 "account",
                 "base"
                 #"document"
                ],
    "data"    : [
                 'security/groups.xml',
                 'security/ir.model.access.csv',
                 'account_payment_view.xml',
                 'res_currency_view.xml',
                 'einvoice_payment_report.xml',
                 'report/l10n_mx_einvoice_payment_report.xml',                 
                 'data/payment_mail_template.xml',
    ],
    'installable'   : True,
    'application'   : False,
    'auto_install'  : False,

}

