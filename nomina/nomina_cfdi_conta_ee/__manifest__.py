# -*- coding: utf-8 -*-

{
    'name': 'Pólizas para Nomina Electrónica',
    'summary': 'Agrega funcionalidades para modificar las pólizas creadas desde la nómina electrónica.',
    'description': '''
    Nomina CFDI Module
    ''',
    'author': 'IT Admin',
    'version': '14.1',
    'category': 'Employees',
    'depends': [
        'om_hr_payroll','om_hr_payroll_account', 'nomina_cfdi_ee', 'hr'
    ],
    'data': [
        'views/hr_salary_view.xml',
        'security/ir.model.access.csv',
        'views/res_config_settings_view.xml',
        'views/hr_payroll_payslip_view.xml',
    ],
    'installable': True,
    'application': False,
    'license': 'AGPL-3',
}
