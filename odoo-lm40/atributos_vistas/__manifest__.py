# -*- encoding: utf-8 -*-


{
    'name' : 'Atributos vistas',
    'description' : """ 


Este modulo permite Agregar los atributos de no_create y no_open en las diferentes vistas


    """,
    'version' : '1.0',
    'author' : 'Qx Unit de México SA de CV',
    'website' : 'http://www.qxunit.com.mx',
    'license' : 'GPL-3',
    'category' : 'Localización Para México',
    'depends' : [
                'base',
                'account',               
                'sale',
                'purchase',
                'stock',
                'product',

                ],
    'init_xml' : [],
    'data' : [
               	            
                    'atributos.xml',
                    

                    ],
    'demo_xml' : [],
    'installable' : True,
    'active' : True,
}
