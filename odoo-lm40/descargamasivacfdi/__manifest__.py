# -*- coding: utf-8 -*-

##############################################################################

{
    "name" : "Descarga masiva CFDI",
    "version" : "1.0",
    "author" : "QX UNIT DE MEXICO SA de CV",
    "category" : "Contabilidad",
    "description": """
    Este modulo permite generar la descarga masiva de CFDI Emitidos y Recibidos

    """,
    "website" : "http://www.qxunit.com.mx",    
    "depends" : [
        
        "account",
        "base", 
        "sat_catalogos",   
        "hr_expense",   
        

        ],
    "data" : [  
        "security/descargas_cfdi.xml",
        "security/ir.model.access.csv",      
        "wizard/wizard_solicita_view.xml",       
        "views/registro_peticiones.xml",
        "views/sequence_view.xml",
        "views/res_company_view.xml",
        "wizard/wizard_compara_compras.xml",
        "views/purchase_invoice_view.xml",
        "wizard/purche_invoice_mo_related.xml",
        "wizard/wizard_status_cfdi.xml",
        "wizard/wizar_compara_gastos.xml",
       
    ],
    
    "installable" : True,
    "active" : False,
}
