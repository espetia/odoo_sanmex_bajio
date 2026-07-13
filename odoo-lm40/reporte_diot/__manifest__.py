# -*- encoding: utf-8 -*-

##############################################################################

{
    "name" : "DIOT",
    "version" : "1.0",
    "author" : "QX UNIT DE MEXICO SA de CV",
    "category" : "Contabilidad",
    "description": """
    

    """,
    "website" : "http://www.qxunit.com.mx",    
    "depends" : [
        "base_vat",
        "account",
        "complementos_contabilidad",
        "pagos",
        

        ],
    "data" : [        
        "security/ir.model.access.csv",       
        "views/account_invoice_view.xml",       
        "views/account_invoice_view.xml",
        "wizard/wizard_diot_report_view.xml",
        "views/ir_sequence_view.xml",
        
    ],
    
    "installable" : True,
    "active" : False,
}
