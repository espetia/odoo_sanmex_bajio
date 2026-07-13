# -*- coding: utf-8 -*-
# Part of Softhealer Technologies.

{
    "name": "Purchase Dynamic Approval | Purchase Order Dynamic Approval | Request For Quotation Dynamic Approval | Dynamic Purchase Approval | Purchase Approval Process | Purchase Order Approval Process",
    "author": "Softhealer Technologies",
    "website": "https://www.softhealer.com",
    "support": "support@softhealer.com",
    "category": "Purchases",
    "summary": "Dynamic Purchase Order Approval Dynamic Purchase Approval Purchase Multi Approval Purchase Order Multiple Approval Purchase Order Double Approval Dynamic PO Approval PO Multi Approval PO Multiple Approval PO Double Approval Dynamic RFQ Approval RFQ Multi Approval RFQ Multiple Approval RFQ Double Approval Dynamic Request For Quotation Approval Request For Quotation Multi Approval Request For Quotation Multiple Approval Request For Quotation Double Approval Purchase Approval Line User Approval Group Approval Dynamic Approval Flexible Approval Process Purchase Order Two Level Approval Purchase Order Two Approval Dynamic  Purchase Order Approval Workflow Multi Level  Purchase Order Approval Workflow Purchase Order Approval Purchase Approval Line User Approval Group Approval Dynamic Approval Flexible Approval Process Dynamic Dynamic Purchase Order Approval Purchase Order Multi Approval Purchase Order Multiple Approval Purchase Order Double Approval User Wise Purchase Order Approval Group Wise Purchase Order Approval Odoo PO Two Level Approval PO Two Approval Dynamic PO Approval Workflow Multi Level PO Approval Workflow PO Approval PO Line User Approval Dynamic PO Approval PO Multi Approval PO Multiple Approval PO Double Approval User Wise PO Approval Group Wise PO Approval Odoo RFQ Two Level Approval RFQ Two Approval Dynamic RFQ Approval Workflow Multi Level RFQ Approval Workflow RFQ Approval RFQ Line User Approval Dynamic RFQ Approval RFQ Multi Approval RFQ Multiple Approval RFQ Double Approval User Wise RFQ Approval Group Wise RFQ Approval Odoo Request For Quotation Two Level Approval Request For Quotation Two Approval Dynamic Request For Quotation Approval Workflow Multi Level Request For Quotation Approval Workflow Request For Quotation Approval Request For Quotation Line User Approval Dynamic Request For Quotation Approval Request For Quotation Multi Approval Request For Quotation Multiple Approval Request For Quotation Double Approval User Wise Request For Quotation Approval Group Wise Request For Quotation Approval Odoo Reject Approval Request",
    "description": """This module allows you to set dynamic and multi-level approvals in the request for quotation/purchase order so each order can be approved by many levels. Purchase orders can be approved based on untaxed/ total amount and approved by particular users or groups they get emails notification about orders that waiting for approval. When a purchase order/RFQ approves or rejects user gets a notification about it.""",
    "version": "14.0.6",
    "depends": ["purchase", "bus","sh_base_dynamic_approval"],
    "data": [
        'security/ir.model.access.csv',
        'data/mail_data.xml',
        'views/purchase_approval_line.xml',
        'views/purchase_approval_config.xml',
        'views/res_config_setting.xml',
        'views/approval_info.xml',
        'views/rejection_wizard.xml',
        'views/inherit_purchase_order.xml',

    ],
    "license": "OPL-1",
    "images": ["static/description/background.png", ],
    "auto_install": False,
    "installable": True,
    "application": True,
    "price": 30,
    "currency": "EUR"
}
