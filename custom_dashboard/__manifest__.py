{
    'name': 'Odoo Custom Dashboard',
    'version': '15.0.0.1',
    'description': '',
    'summary': '',
    'author': '',
    'website': '',
    'license': 'LGPL-3',
    'category': '',
    'depends': [
        'base', 'sale', 'purchase','product', 'web','board'
    ],
    'data': [
        'views/dashboard_view.xml',
        'views/dashboard_menu.xml',
    ],
    'auto_install': False,
    'application': True,
    'assets': {
        'web.assets_qweb': [
            'custom_dashboard/static/src/components/**/*.xml',
        ],
        'web.assets_backend': [
            'custom_dashboard/static/src/components/**/*.js',
            'custom_dashboard/static/src/components/**/*.xml',
            'custom_dashboard/static/src/components/**/*.scss',
            #'https://cdnjs.cloudflare.com/ajax/libs/Chart.js/4.4.1/chart.umd.min.js'
        ],
    }
}