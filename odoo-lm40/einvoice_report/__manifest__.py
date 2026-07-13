# -*- encoding: utf-8 -*-

{
    "name" : "Factura",
    "version" : "1.0",
    "author" : "Qx Unit de México sa de cv",
    "category" : "Contabilidad",
    "description" : """Factura Electronica
    """,
    "website" : "http://www.qxunit.com.mx",    
    "depends" : [
        "account", 
        "sale",
        "sat_catalogos"
    ],
    "data" : [        
        "factura_report.xml",
        "report/invoice_facturae.xml",
    ],
    "installable" : True,
    "active" : False,
}
