# -*- encoding: utf-8 -*-
###########################################################################


{
    'name' : 'Complemento Carta Porte',
    'description' : """ 


Este modulo integra nuevos Catalogos Para la generación del complemento de carta porte, asi como el procesod de timbrado del mismo


    """,
    'version' : '1.0',
    'author' : 'Qx Unit de México SA de CV',
    'website' : 'http://www.qxunit.com.mx',
    'license' : 'GPL-3',
    'category' : 'Accounting',
    'depends' : [
                'base',
                'account',
                'sat_catalogos',
                'hr',
                'fleet',
                
                
                
                

                ],
    'init_xml' : [],
    'data' : [
                                       
                    
                    'security/ir.model.access.csv',                   
		            'views/catalogoscp_views.xml',                    
                    'wizard/upload_data_view.xml',
                    'views/sale_order_view.xml',
                    'views/employee_view.xml',
                    'views/stock_picking_view.xml',
                    'views/update_vencimiento.xml',                                                           
                    'reporte/reporte_factura_traslado.xml',                    
                    #'views/res_company_view.xml',                    
                    #'views/sale_view.xml',
                    #'views/purchase_view.xml',
                    #'views/account_journal_view.xml',
                    #'data/data_view.xml',
                    #'data/cancelaciones_plantilla.xml',
                    #'views/cfdi_xml.xml',
                    #'views/ir_sequence_view.xml'
                    
                    

                    ],
    'demo_xml' : [],
    'installable' : True,
    'active' : True,
}
