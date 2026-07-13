#!/usr/bin/python
# -*- encoding: utf-8 -*-
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Affero General Public License as published by
#    the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Affero General Public License for more details.
#
#    You should have received a copy of the GNU Affero General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
################################################################################
{
    "name" : "Categoria de Impuestos",
    "version" : "1.0",
    "depends" : ["account"
                 ],
    "author" : "Qx Unit de México SA de CV",
    #"license" : "AGPL-3",
    "description" : """
    """,
    "website" : "http://www.qxunit.com.mx",
    "category" : "Impuestos",    
    
    "data" : [       
        
        'account_tax_category_view.xml',
        'data/account_tax_category_data.xml',
        'security/ir.model.access.csv',
    ],
    "active": False,
    "installable": True,
}

