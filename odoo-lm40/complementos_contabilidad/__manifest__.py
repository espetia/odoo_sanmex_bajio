# -*- encoding: utf-8 -*-



{
    'name' : 'Contabilidad electrónica',
    'description' : """
    
         """,
    'version' : '1.0',
    'author' : 'ASTI & Qx Unit de México',
    'website' : 'http://www.qxunit.com.mx',
    #'license' : 'GPL-3',
    'category' : 'Contabilidad',
    'depends' : ['base', 
                 'account',                 
                 'account_check_printing', 
                 #'account_cancel',                
                 'sat_catalogos',
                 'pagos'
                ],
    'data' : [  
                'security/groups.xml',
                'security/ir.model.access.csv',
                'views/ir_config_parameter.xml',                      
                'views/account_moveline_fit_view.xml',                
                'views/menu.xml',              
                'views/account_move_fit_view.xml',
                'wizard/files_generator_view.xml',
                'views/ir_sequence_view.xml',
                'wizard/movelines_info_manager_view.xml',                    
                'loadable_data/complements.xml',
                'views/restrictive_actions.xml',                
                'views/payment_fit_view.xml'                         
                
                ],
    'demo_xml' : [],
    'installable' : True,
    'auto_install' : False
}

