# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
from odoo.exceptions import UserError


class PurchaseOrder(models.Model):
    _inherit = "purchase.order"

    available_budget = fields.Float(string="Disponible para compra", compute="get_available_budget", store=True)
    project_id = fields.Many2one(
        compute="_compute_project_id",
        inverse="_inverse_project_id",
        comodel_name="account.analytic.account",
        string="Cuenta Analitica",
        readonly=True,
        states={"draft": [("readonly", False)]},
        store=True,
        help="Centro de costos asociado a esta compra.",
    )
    payment_type = fields.Selection(
        [
            ("1", "Efectivo"),
            ("2", "Credito Proveedor"),
            ("3", "American Express"),
            ("4", "Pago Inmediato"),
            ("5", "Gastos fijos"),
            ("6", "Gastos Dirección"),
            ("7", "Compras amex domiciliados"),
        ],
        string="Forma de Pago",
    )
    in_budget = fields.Boolean(string="Presupuesto disponible")
    journal_id = fields.Many2one(
        "account.journal",
        string="Diario de pago",
        required=False,
        readonly=True,
        states={"draft": [("readonly", False)]},
        domain="[('type', 'in', ('bank', 'cash'))]",
    )
    fortnight_pay = fields.Selection(
        [
            ("1", "Q1"),
            ("2", "Q2"),
        ],
        string="Quincena de pago",
    )
    date_invoice_partner = fields.Date(
        string="Fecha de factura")

    @api.depends("project_id", "amount_total")
    def get_available_budget(self):
        for record in self:
            if record.project_id:
                budget_lines = self.env["budget.lines"].search(
                    [
                        ("analytic_account_id", "=", record.project_id.id),
                        ("date_to", ">=", record.date_planned),
                        ("date_from", "<=", record.date_planned),
                    ]
                )

                real_available_budget = budget_lines.planned_amount - budget_lines.purchase_amount
                if real_available_budget < 0:
                    record.available_budget = abs(real_available_budget)
                else:
                    record.available_budget = 0
                    if budget_lines.purchase_amount == 0:
                        record.available_budget = abs(budget_lines.planned_amount)
            else:
                record.available_budget = 0

            if record.available_budget > record.amount_total:
                record.in_budget = True
            else:
                record.in_budget = False

    # remove bloqueo
    # def button_confirm(self):
    #    for order in self:
    #        if not order.project_id.management:
    #            if order.available_budget < order.amount_untaxed:
    #                raise UserError(
    #                    _("Esta compra excede el presupuesto disponible de (%s) para el centro de costos (%s) en el periodo seleccionado. Favor de validar.") % (
    #                    order.available_budget, order.project_id.name))
    #    return super(PurchaseOrder, self).button_confirm()

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

    def _prepare_invoice(self):
        """Prepare the values to create the invoice."""
        self.ensure_one()
        invoice_vals = super(PurchaseOrder, self)._prepare_invoice()
        if self.date_invoice_partner:
            invoice_vals["invoice_date"] = self.date_invoice_partner
        return invoice_vals


class PurchaseOrderLine(models.Model):
    _inherit = "purchase.order.line"

    vehicle_id = fields.Many2one("fleet.vehicle", string="Vehiculo")
    invoice_status = fields.Selection(related="order_id.invoice_status", store=True)
    amount_to_invoice = fields.Float(string="Monto a facturar", compute="compute_amount_to_invoice")

    @api.depends("product_qty")
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
        res["vehicle_id"] = self.vehicle_id.id
        return res


class AccoountBudgetLines(models.Model):
    _inherit = "budget.lines"

    purchase_amount = fields.Float(string="En compras", compute="get_open_purchases")
    available_budget = fields.Float(string="Disponible", compute="get_available_budget")
    effective_amount = fields.Float(string="Ejercido", compute="get_effective_amount")

    @api.depends("analytic_account_id")
    def get_available_budget(self):
        for record in self:
            record.available_budget = record.planned_amount - record.effective_amount

    def get_open_purchases(self):
        for line in self:
            purchase_lines = self.env["purchase.order"].search(
                [
                    ("state", "in", ["purchase", "done"]),
                    # ('invoice_status', '!=', 'invoiced'),
                    ("date_planned", ">=", line.date_from),
                    ("date_planned", "<=", line.date_to),
                    ("project_id", "=", line.analytic_account_id.id),
                ]
            )

            if purchase_lines:
                line.purchase_amount = sum(purchase_lines.mapped("order_amount_residual")) * -1
            else:
                line.purchase_amount = 0.00

    def get_effective_amount(self):
        for line in self:
            paid_lines = self.env["account.move.line"].search(
                [
                    ("date", ">=", line.date_from),
                    ("date", "<=", line.date_to),
                    ("analytic_account_id", "=", line.analytic_account_id.id),
                    ("payment_id", "!=", False),
                    ("matching_number", "!=", False),
                ]
            )
            if paid_lines:
                # line.effective_amount = sum(paid_lines.mapped("debit")) * -1
                # The effective amount is the sum of all debit amounts
                efecctive_amount = sum(paid_lines.mapped("debit")) * -1
                efecctive_fixed_amount = sum(paid_lines.mapped("credit"))
                line.effective_amount = efecctive_amount + efecctive_fixed_amount
            else:
                line.effective_amount = 0.00


# class AccountMoveLine(models.Model):
#   _inherit = 'account.move.line'
#
#    paid_amount = fields.Float(string='Pagado', compute='compute_paid_amount')
#
#    @api.depends('price_total', 'amount_residual')
#    def compute_paid_amount(self):
#        for record in self:
#            record.paid_amount = record.price_total - record.amount_residual
