# -*- coding: utf-8 -*-
from odoo import fields, models

class PurchaseOrderLine(models.Model):
    _inherit = 'purchase.order.line'

    # Fields from purchase.order made available on the line
    # We add store=True to make them searchable and groupable

    date_order = fields.Datetime(
        related='order_id.date_order',
        string='Order Date',
        store=True,
        readonly=True
    )
    partner_id = fields.Many2one(
        related='order_id.partner_id',
        string='Provider',
        store=True,
        readonly=True
    )
    payment_type = fields.Selection(
        related='order_id.payment_type',
        string='Payment Type',
        store=True,
        readonly=True
    )
    internal_note = fields.Text(
        related='order_id.internal_note',
        string='Internal Note',
        readonly=True
    )
    exceptional_purchase_order = fields.Boolean(
        related='order_id.exceptional_purchase_order',
        string='Exceptional Purchase',
        store=True,
        readonly=True
    )
    project_id = fields.Many2one(
        related='order_id.project_id',
        string='Analytic Account',
        store=True,
        readonly=True
    )
    order_reference = fields.Char(
        related='order_id.name',
        string='Order Reference',
        store=True,
        readonly=True
    )
    payment_date = fields.Date(
        related='order_id.payment_date',
        string='Payment Date',
        store=True,
        readonly=True
    )
    fortnight_pay = fields.Selection(
        related='order_id.fortnight_pay',
        string='Fortnight Pay',
        store=True,
        readonly=True
    )
    journal_id = fields.Many2one(
        related='order_id.journal_id',
        string='Journal',
        store=True,
        readonly=True
    )
