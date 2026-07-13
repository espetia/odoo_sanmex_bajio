# -*- coding: utf-8 -*-
{
    'name': 'Custom Hr Attendance Sanmex',
    'version': '',
    'description': """ Custom Hr Attendance Sanmex """,
    'summary': """ Add department in hr attendance """,
    'author': '',
    'website': '',
    'category': '',
    'depends': ['base', 'hr_attendance','tis_hr_biometric_attendance',],
    'data': [
        'views/hr_attendance_filter_view.xml',
        'views/attendace_log_view.xml',
    ],
    'application': True,
    'installable': True,
    'auto_install': False,
    'license': 'LGPL-3',
}