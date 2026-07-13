# -*- encoding: utf-8 -*-
###########################################################################
#    Module Writen to OpenERP, Open Source Management Solution
#
#    Copyright (c) 2014 Argil Consulting - http://www.argil.mx
############################################################################
#    Coded by: Israel Cruz Argil (israel.cruz@argil.mx)
############################################################################
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Affero General Public License as
#    published by the Free Software Foundation, either version 3 of the
#    License, or (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Affero General Public License for more details.
#
#    You should have received a copy of the GNU Affero General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################
{
    'name': 'Reportes Contables Mexico',
    'version': '1',
    "author" : "Argil Consulting",
    "category" : "Account",
    'description': """
Reportes Contables comunmente usados en Mexico
==============================================

Este modulo esta enfocado cuando se maneja multicompany y permite consolidar cuentas de las sucursales hacia la empresa central

        Diversos informes segun los requerimientos de Mexico, basados en 13 periodos al año 
        (12 meses naturales y Periodo Inicial), 
        donde el periodo 0 es de apertura/cierre.
        Los informes son:
	   - Balanza Mensual de Comprobacion
	   - Auxiliar de cuentas (desde la Balanza de comprobacion)
	   - Auxiliar de cuentas
	   - Configurador de Reportes Personalizados
	   - Generador de Reportes Personalizados

	NOTAS IMPORTANTES:
	- Estos reportes funcionan tomando en cuenta lo siguiente:
		+ Deben usarse 13 periodos por cada periodo Fiscal.
		+ El nombre de los periodos es importante, de manera que deben tener orden alfabetico, por ejemplo:
		
        * 01/2012
		* 02/2012
		* 03/2012
		* 04/2012
		* 05/2012
		* 06/2012
		* 07/2012
		* 08/2012
		* 09/2012
		* 10/2012
		* 11/2012
		* 12/2012
        * 13/2012	=> Marcado como periodo de cierre
		

    """,
    "website" : "http://www.qxunit.com.mx",
    "license" : "AGPL-3",
    "depends" : ["account",
                 "Plan_contable",
                 #"jasper_reports",
                 #"qweb_usertime",
                 "account_period_and_fiscalyear"],
    "data" : [#"security/ir.model.access.csv",
    		  "account_mx_reports_view.xml",
              "report/report_balanza_mensual.xml",
              "report/report_auxiliar_cuentas.xml",
              #"
             ],
    "installable" : True,
    #"active" : False,
}
