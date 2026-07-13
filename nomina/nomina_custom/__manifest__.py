# -*- coding: utf-8 -*-

{
    'name': 'Cambios Nomina Electrónica para México CFDI v1.2',
    'summary': 'Agrega funcionalidades para timbrar la nómina electrónica en México con las nuevas disposiciones',
    'description': '''
    Nomina CFDI Module
    ''',
    'author': 'Qx Unid de México',
    'version': '1.0',
    'category': 'Employees',
    'depends': [
        'nomina_cfdi_ee',
    ],
    'data': [
        
        'views/hr_payroll_view.xml',
    ],
    'installable': True,
    'application': False,
    'license': 'AGPL-3',
}
