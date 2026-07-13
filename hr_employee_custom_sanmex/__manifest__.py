# -*- coding: utf-8 -*-
{
    'name': 'Modulo para personalización de RH',
    'version': '15.0.1.0',
    'summary': """ Se realizan personalizaciones en el modulo de Recursos Humanos""",
    'author': 'Jorge Chuc',
    'website': '',
    'category': '',
    'depends': ['hr', 'base', 'contacts'],
    "data": [
        "report/paperformat.xml",
        "views/hr_employee_views.xml",
        "report/custom_card_employee.xml",
    ],
    'installable': True,
    'license': 'LGPL-3',
}
