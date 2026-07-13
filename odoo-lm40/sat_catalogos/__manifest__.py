# -*- encoding: utf-8 -*-
###########################################################################
#    Module Writen to Odoo
#
#    All Rights Reserved.
##############################################################################

{
    'name' : 'Catalogos SAT CFDI 3.3',
    'description' : """ 


Este modulo integra nuevos Catalogos de direccion para utilizarse en el CFDI 3.3


    """,
    'version' : '1.0',
    'author' : 'Qx Unit de México SA de CV',
    'website' : 'http://www.qxunit.com.mx',
    'license' : 'GPL-3',
    'category' : 'Localización Para México',
    'depends' : [
                'base',
                'account',
                'stock_account',              
                'sales_team',                
                #'document',
                #'account_cancel',
                
                
                

                ],
    'init_xml' : [],
    'data' : [
                                       
                    'security/l10n_mx_facturae_security_groups.xml',
                    'security/ir.model.access.csv',
                    'views/menu_view.xml',
		            'views/catalogo_sat.xml',                    
                    'views/eaccount_bank_view.xml',
                    'views/product_view.xml',
                    'views/account_invoice_view.xml',
                    'wizard/upload_data_view.xml',
                    'views/res_partner_view.xml',
                    'views/res_partner1_view.xml',                                                           
                    'views/res_partner_bank_view.xml',                    
                    'views/res_company_view.xml',                    
                    'views/sale_view.xml',
                    'views/purchase_view.xml',
                    'views/account_journal_view.xml',
                    'data/data_view.xml',
                    'data/cancelaciones_plantilla.xml',
                    'views/cfdi_xml.xml',
                    'views/ir_sequence_view.xml'
                    
                    

                    ],
    'demo_xml' : [],
    'installable' : True,
    'active' : True,
}
