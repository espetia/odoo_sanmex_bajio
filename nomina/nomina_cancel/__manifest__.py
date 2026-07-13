# -*- encoding: utf-8 -*-
##############################################################################

{
    'name': 'Acount Payslip Cancel without removing Account Move',
    'version': '1',
    "author" : "Qx Unit de México",
    "category" : "Account",
    'description': """
Cancelación de Nómina
===================================================



    """,
    "website" : "http://www.qxunit.com.mx",
    "license" : "AGPL-3",
    "depends" : ['om_hr_payroll', 'account', 'nomina_cfdi_ee', 'cancelaciones_cfdi4'],
    "data" : [
              'account_nomina_view.xml',
              
             
                    ],
    "installable" : True,
    "active" : False,
}
