# -*- encoding: utf-8 -*-
###########################################################################
#    Module Writen to Odoo
#
#    All Rights Reserved.
##############################################################################

{
    'name' : 'Webservice',
    'description' : """ 


Este modulo Permite la conexión al Webservice para la carga de  Catalogos SAT CFDI 3.3


    """,
    'version' : '1.0',
    'author' : 'Qx Unit de México SA de CV',
    'website' : 'http://www.qxunit.com.mx',
    'license' : 'GPL-3',
    'category' : 'Localización Para México',
    'depends' : [
                'base',
                'product',
                'sale',
                'purchase'
                ],
    
    'data' : [
                                       
                    'views/webserviceconection_view.xml',
                    'views/webservice_view.xml',
                    'views/historial_actua_views.xml',
                     'views/ir_sequence_view.xml',
                    'security/ir.model.access.csv',
                    
                    

                    ],
    
    'installable' : True,
    'active' : True,
}
