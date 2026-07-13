# -*- encoding: utf-8 -*-
###########################################################################
#    Module Writen to Odoo
#
#    All Rights Reserved.
##############################################################################

{
    'name' : 'Campos Studio',
    'description' : """ 


Campos Studio


    """,
    'version' : '1.0',
    'author' : 'Qx Unit de México SA de CV',
    'website' : 'http://www.qxunit.com.mx',
    'license' : 'GPL-3',
    'category' : 'Sale and Accounting',
    'depends' : [
                'base',
                'account',
                'sale',
                'sale_renting'
                 
                
                
                

                ],
    'init_xml' : [],
    "data": [
        #"security/ir.model.access.csv",
        "views/sale_order.xml",
        "reports/sale_renting_out_view_report.xml",
        "reports/sale_renting_return_view_report.xml",
        'reports/sale_renting_relocation_view_report.xml',
        'reports/sale_renting_sheet_view_report.xml',
    ],
    'demo_xml' : [],
    'installable' : True,
    'active' : True,
}
