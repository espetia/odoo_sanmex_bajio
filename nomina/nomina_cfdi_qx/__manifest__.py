# -*- coding: utf-8 -*-

{
    'name': 'Nomina Electrónica para México CFDI v1.2',
    'summary': 'Agrega funcionalidades para timbrar la nómina electrónica en México.',
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
        'security/security.xml',
        'views/hr_contract_view.xml',
        'views/hr_payroll_payslip_view.xml',
    ],
    'installable': True,
    'application': False,
    'license': 'AGPL-3',
}
