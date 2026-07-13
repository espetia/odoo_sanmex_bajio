# -*- encoding: utf-8 -*-
###########################################################################
#    Module Writen to Odoo
#
#    All Rights Reserved.
##############################################################################

{
    'name' : 'Control de Anticipos',
    'description' : """ 


Este modulo permite llevar un control de anticipos para su aplicación en facturas


    """,
    'version' : '1.0',
    'author' : 'Qx Unit de México SA de CV',
    'website' : 'http://www.qxunit.com.mx',
    'license' : 'GPL-3',
    'category' : 'Localización Para México',
    'depends' : [
                #'base',
                'account',               
                'sat_catalogos'

                ],
    'init_xml' : [],
    'data' : [
               	    'security/ir.model.access.csv',        
                    'anticipos.xml',
                    

                    ],
    'demo_xml' : [],
    'installable' : True,
    'active' : True,
}
