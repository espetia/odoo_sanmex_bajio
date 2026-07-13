# -*- coding: utf-8 -*-

{
    'name': 'Formulas de Nomina Electrónica para México CFDI v1.2',
    'summary': 'Agrega reglas salariales para la nómina electrónica en México.',
    'description': '''
    Nomina CFDI Module
    ''',
    "website": "http://www.qxunit.com.mx",
    'author': 'Qx Unit de Mexico',
    'version': '1.0',
    'category': 'Employees',
    'depends': [
        'nomina_cfdi_ee'
    ],
    'data': [
        'data/reglas_salariales_data.xml',
    ],
    'installable': True,
    'application': False,
    'license': 'AGPL-3',
}
