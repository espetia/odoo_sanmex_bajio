# -*- encoding: utf-8 -*-


{
    'name' : 'Cuentas',
    'description' : """ 


Este modulo permite Agregar los filtros en cuentas de tipo vista


    """,
    'version' : '1.0',
    'author' : 'Qx Unit de México SA de CV',
    'website' : 'http://www.qxunit.com.mx',
    'license' : 'GPL-3',
    'category' : 'Localización Para México',
    'depends' : [
                'base',
                'account',               
                #'sale',
                #'account_asset',
                'stock',
                'product',

                ],
    'init_xml' : [],
    'data' : [
               	            
                    'atributos_cuentas.xml',
                    

                    ],
    'demo_xml' : [],
    'installable' : True,
    'active' : True,
}
