# -*- coding: utf-8 -*-
{
    "name": "Registro de documentos de cumplimiento legales de Sanmex",
    "version": "15.0.1.0.0",
    "summary": """ Registro de documentos de cumplimiento legales de Sanmex como seguros, licencias, permisos, etc.""",
    "author": "Jorge Chuc",
    "website": "https://muyul.mx/",
    "category": "",
    "depends": [
        "base",
        "hr",
        "fleet",
        "hr_employee_custom_sanmex"
    ],
    "data": [
        "security/compliance_documents_manager_security.xml",
        "security/ir.model.access.csv",
        "views/compliance_partner_manager_views.xml",
        "views/compliance_document_line_views.xml",
        "views/fleet_vehicle_log_contract_views.xml",
        "views/hr_employee_views.xml",
        "views/type_compliance_document_views.xml",
        "views/fleet_vehicle_views.xml",
    ],
    "application": True,
    "installable": True,
    "auto_install": False,
    "license": "LGPL-3",
}
