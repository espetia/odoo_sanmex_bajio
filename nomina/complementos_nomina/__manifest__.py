# -*- coding: utf-8 -*-
{
    'name': 'Configuraciones adicionales para el funcionamiento de la generación de nómina',
    'summary': 'Agregar campos, secuencias, y edición de reportes actuales para la gestión de la nómina',
    'description': '''
    * Validación masiva de incidencias (faltas, incapacidades, horas extra, vacaciones) en la sección de movimientos.
    * Adición de campo de número de nómina del empleado y autorización masiva de deducciones recurrentes.
    * Modificación de reporte de listado de raya y recibos de nómina.
    * Adición de campo para generar automaticamente cuando un empleado cumpla un año en la empresa.
    * Personalizaciones para nomina_cfdi_extras. 
    * Agrega funcionalidades para timbrar la nómina electrónica en México.'
    * genera reporte de incidencias que se tuvieron los empleados durante el periodo de nómina para incidencias de Faltas, Incapacidades, Vacaciones, Dias festivos, Retardos y Horas Extra, se genera un reporte por incidencia.
    * Módulo permite generar un reporte general de la antigüedad del personal conforme a la fecha de alta
    * Este modulo genera archivo TXT de Nomina de los Empleados
    ''',
    "website": "http://www.qxunit.com.mx",
    'author': 'QX Unit de México',
    'version': '1.0',
    'category': 'employees',
    'depends': [
        'nomina_cfdi_ee',
        'nomina_cfdi_extras_ee',
        'hr_contract',
    ],
    'data': [
        'security/security.xml',
        'security/ir.model.access.csv',
        'wizard/importar_movimientos_faltas_view.xml',
        'wizard/importar_movimientos_vacaciones_view.xml',
        'wizard/importar_movimientos_horas_extras_view.xml',
        'wizard/importar_movimientos_retardos_view.xml',
        'wizard/importar_movimientos_incapacidades_view.xml',
        'wizard/importar_movimientos_feriados_view.xml', 
        'wizard/hr_payroll_payslips_by_employees_views.xml',       
        'views/menu.xml',
        'views/employee_loan_view.xml',
        'views/hr_employee_view.xml',
        'views/hr_contract_view.xml',        
        'views/hr_payslip_input_view.xml',
        'views/hr_payslip_run_view.xml', 
        'views/view_txt_nomina.xml',       
        'report/payslip_batches_report_2.xml',
        'report/report_payslip_2.xml',
        'report/reporte_incidencia_h_e.xml',
        'report/reporte_incidencias_df.xml',
        'report/reporte_incidencias_faltas.xml',
        'report/reporte_incidencias_inc.xml',
        'report/reporte_incidencias_ret.xml',
        'report/reporte_incidencias_vac.xml',
        'report/report_vacaciones_utilizadas_x_empleado.xml',
        'data/sequence_payslip_employee.xml',
        'views/hr_views.xml',
        'views/credito_infonavit_views.xml',

    ],
}