# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
from odoo.exceptions import UserError

class PurchaseOrder(models.Model):
    _inherit = 'purchase.order'

    available_budget = fields.Float(string='Presupuesto disponible', compute='get_available_budget')
    project_id = fields.Many2one(compute="_compute_project_id", inverse="_inverse_project_id", comodel_name="account.analytic.account",
        string="Cuenta Analitica", readonly=True, states={"draft": [("readonly", False)]}, store=True, help="Centro de costos asociado a esta compra.",)

    @api.depends('project_id')
    def get_available_budget(self):
        for record in self:
            if record.state in ('draft', 'sent', 'to_approve') and record.project_id:
                budget_lines = self.env['budget.lines'].search([
                    ('analytic_account_id', '=', record.project_id.id),
                    ('date_to', '>=', record.date_planned),
                    ('date_from', '<=', record.date_planned),
                ])
                real_available_budget = sum(budget_lines.mapped('planned_amount')) - sum(budget_lines.mapped('practical_amount')) - sum(
                    budget_lines.mapped('purchase_amount'))
                if real_available_budget < 0:
                    record.available_budget = abs(real_available_budget)
                else:
                    record.available_budget = 0.0
            else:
                record.available_budget = 0.0

    def button_confirm(self):
        for order in self:
            if order.available_budget < order.amount_untaxed:
                raise UserError(
                    _("Esta compra excede el presupuesto disponible de (%s) para el centro de costos (%s) en el periodo seleccionado. Favor de validar.") % (
                    order.available_budget, order.project_id.name))
        return super(PurchaseOrder, self).button_confirm()

    @api.depends("order_line.account_analytic_id")
    def _compute_project_id(self):
        """If all order line have same analytic account set project_id.
        If no lines, respect value given by the user.
        """
        for po in self:
            if po.order_line:
                al = po.order_line[0].account_analytic_id or False
                for ol in po.order_line:
                    if ol.account_analytic_id != al:
                        al = False
                        break
                po.project_id = al

    def _inverse_project_id(self):
        """When set project_id set analytic account on all order lines"""
        for po in self:
            if po.project_id:
                po.order_line.write({"account_analytic_id": po.project_id.id})

    @api.onchange("project_id")
    def _onchange_project_id(self):
        """When change project_id set analytic account on all order lines"""
        if self.project_id:
            self.order_line.update({"account_analytic_id": self.project_id.id})



class PurchaseOrderLine(models.Model):
    _inherit = 'purchase.order.line'

    vehicle_id = fields.Many2one('fleet.vehicle', string='Vehiculo')
    invoice_status = fields.Selection(related="order_id.invoice_status", store=True)
    amount_to_invoice = fields.Float(string='Monto a facturar', compute='compute_amount_to_invoice')

    @api.depends('product_qty')
    def compute_amount_to_invoice(self):
        for record in self:
            if record.product_id:
                amount_to_invoice = ((record.product_qty - record.qty_invoiced) * record.price_unit) * -1
                if amount_to_invoice < 0:
                    record.amount_to_invoice = amount_to_invoice
                else:
                    record.amount_to_invoice = 0

    @api.model
    def _prepare_account_move_line(self, move=False):
        res = super(PurchaseOrderLine, self)._prepare_account_move_line(move=move)
        res['vehicle_id'] = self.vehicle_id.id
        return res


class AccoountBudgetLines(models.Model):
    _inherit = 'budget.lines'

    purchase_amount = fields.Float(string='En compras', compute='get_open_purchases')
    available_budget = fields.Float(string='Disponible', compute='get_available_budget')

    @api.depends('analytic_account_id')
    def get_available_budget(self):
        for record in self:
            record.available_budget = record.planned_amount - record.practical_amount - record.purchase_amount

    def get_open_purchases(self):
        for line in self:
            purchase_lines = self.env['purchase.order.line'].search([
                ('state', 'in', ['purchase', 'done']),
                # ('invoice_status', '!=', 'invoiced'),
                ('date_planned', '>=', line.date_from),
                ('date_planned', '<=', line.date_to),
                ('account_analytic_id', '=', line.analytic_account_id.id)
            ])

            if purchase_lines:
                line.purchase_amount = sum(purchase_lines.mapped('amount_to_invoice'))
            else: line.purchase_amount = 0.00





