
{
    "name": "Account Fiscalyear and Periods", 
    "version": "1.0", 
    "author": "Argil Consulting", 
    "category": "Account", 
    "description": """

Account Fiscalyear and Periods
==============================

This module adds "dummy" Fiscal year and Periods for migrating IFRS and Accounting Reports.

Fiscal year in México is practically a Natural Year.

Periods in Fiscal year there must be 13 periods, for example, for Fiscal year 2016 we need:


Period name => Opening/Closing Period

-  00/2016    =>     Checked
-  01/2016    =>   Not Checked
-  02/2016    =>   Not Checked
-  03/2016    =>   Not Checked
-  04/2016    =>   Not Checked
-  05/2016    =>   Not Checked
-  06/2016    =>   Not Checked
-  07/2016    =>   Not Checked
-  08/2016    =>   Not Checked
-  09/2016    =>   Not Checked
-  10/2016    =>   Not Checked
-  11/2016    =>   Not Checked
-  12/2016    =>   Not Checked


    """, 
    "website": "http://www.qxunit.com.mx", 
    "license": "AGPL-3", 
    "depends": [
        "account", 
    ], 
    "demo": [], 
    "data": ["account_view.xml",
             "security/ir.model.access.csv",
            ], 
    "js": [], 
    "css": [], 
    "qweb": [], 
    "installable": True, 
    #"auto_install": False, 
    #"active": False
}