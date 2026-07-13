{
    'name': 'Purchase Order Payment Status',
    'summary': 'Show Payment Status on Purchase Order Tree and Purchase Order Form. '
               'Do a payment on Purchase Order Form',
    'description': 'Show Payment Status on Purchase Order Tree and Purchase Order Form. '
                   'Do a payment on Purchase Order Form',
    'author': "Sonny Huynh",
    'category': 'Purchase',
    'version': '0.1',
    'depends': ['purchase'],

    'data': [
        'views/form_view.xml',
    ],
    'qweb': [
        "static/src/xml/account_payment.xml",
    ],
    # only loaded in demonstration mode
    'demo': [],
    'images': [
        'static/description/banner.png',
    ],
    'license': 'OPL-1',
    'price': 30.00,
    'currency': 'EUR',
}