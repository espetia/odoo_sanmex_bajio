# -*- coding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) 2015 S&C (<http://sysneoconsulting.com>).
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
    'name': "Product List Price",
    'summary': "",
    'description': """

Funcionalidades:
================

- Permite consultar el tipo de cambio de acuerdo al Diario OFICIAL DE LA FEREDARICION


        """,
    'author': "Javier Salazar",
    'website': "https://www.qxunit.com.mx",
    'category': 'product',
    'version': '1.0',
    'depends': ['currency_rate_live'],
    'data': [
    ],
    'installable': True,
    'aplication': True,
}
