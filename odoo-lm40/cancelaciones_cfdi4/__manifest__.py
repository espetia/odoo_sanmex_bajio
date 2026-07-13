# -*- encoding: utf-8 -*-
###########################################################################
#    Module Writen to Odoo
#
#    All Rights Reserved.
##############################################################################

{
    'name' : 'Cancelaciones CFDI 4.0',
    'description' : """ 


        Nuevo esquema de Cancelaciones


    """,
    'version' : '1.0',
    'author' : 'Qx Unit de México SA de CV',
    'website' : 'http://www.qxunit.com.mx',
    'license' : 'GPL-3',
    'category' : 'Localización Para México',
    'depends' : [
                
                'account',
                'sat_catalogos',   
                'pagos',           
                
                
                
                

                ],
    'init_xml' : [],
    'data' : [
                                       
                    
                    'security/ir.model.access.csv',
                    'cancelacionescfdi4.xml',
		            
                    
                    

                    ],
    'demo_xml' : [],
    'installable' : True,
    'active' : True,
}
