# -*- coding: utf-8 -*-
from odoo import api, SUPERUSER_ID, fields
from datetime import date, timedelta

def post_init_hook(cr, registry):
    env = api.Environment(cr, SUPERUSER_ID, {})
    
    # Calculate start date: first day of last month
    today = date.today()
    first_day_current_month = today.replace(day=1)
    last_month_end = first_day_current_month - timedelta(days=1)
    first_day_last_month = last_month_end.replace(day=1)
    
    # Run the check from the first day of last month
    env['customer.status.log']._check_customer_status_by_date(first_day_last_month)
