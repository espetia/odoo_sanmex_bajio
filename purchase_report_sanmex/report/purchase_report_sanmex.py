# -*- coding: utf-8 -*-
import re

from odoo import api, fields, models, tools
from odoo.exceptions import UserError
from odoo.osv.expression import AND, expression


class PurchaseReportSanmex(models.Model):
    _name = "purchase.report.sanmex"
    _description = "Reporte de compras San Mex"
    _auto = False
    _order = "date_order desc, price_total desc"

    date_order = fields.Datetime(
        "Fecha de orden",
        readonly=True,
        help="Depicts the date when the Quotation should be validated and converted into a purchase order.",
    )
    state = fields.Selection(
        [
            ("draft", "Solicitud de cotización"),
            ("sent", "Solicitud de cotización enviada"),
            ("to approve", "Para aprobar"),
            ("purchase", "Orden de compra"),
            ("done", "Completado"),
            ("cancel", "Cancelado"),
        ],
        "Status",
        readonly=True,
    )
    product_id = fields.Many2one("product.product", "Producto", readonly=True)
    partner_id = fields.Many2one("res.partner", "Proveedor", readonly=True)
    trade_name = fields.Char("Nombre comercial", readonly=True)
    date_approve = fields.Datetime("Fecha de confirmación", readonly=True)
    product_uom = fields.Many2one("uom.uom", "Unidad de medida", required=True)
    company_id = fields.Many2one("res.company", "Empresa", readonly=True)
    currency_id = fields.Many2one("res.currency", "Moneda", readonly=True)
    user_id = fields.Many2one("res.users", "Represetante de compra", readonly=True)
    delay = fields.Float(
        "Días de confirmación",
        digits=(16, 2),
        readonly=True,
        group_operator="avg",
        help="Amount of time between purchase approval and order by date.",
    )
    delay_pass = fields.Float(
        "Días para recibir",
        digits=(16, 2),
        readonly=True,
        group_operator="avg",
        help="Amount of time between date planned and order by date for each purchase order line.",
    )
    avg_days_to_purchase = fields.Float(
        "Promedio de días de compra",
        digits=(16, 2),
        readonly=True,
        store=False,  # needs store=False to prevent showing up as a 'measure' option
        help="Amount of time between purchase approval and document creation date. Due to a hack needed to calculate this, \
              every record will show the same average value, therefore only use this as an aggregated value with group_operator=avg",
    )
    price_total = fields.Float("Total", readonly=True)
    price_average = fields.Float("Costo promedio", readonly=True, group_operator="avg", digits="Product Price")
    nbr_lines = fields.Integer("# de lineas", readonly=True)
    category_id = fields.Many2one("product.category", "Categoría de producto", readonly=True)
    product_tmpl_id = fields.Many2one("product.template", "Product Template", readonly=True)
    country_id = fields.Many2one("res.country", "País", readonly=True)
    fiscal_position_id = fields.Many2one("account.fiscal.position", string="Position fiscal", readonly=True)
    account_analytic_id = fields.Many2one("account.analytic.account", "Cuenta analitica", readonly=True)
    commercial_partner_id = fields.Many2one("res.partner", "Entidad comercial", readonly=True)
    weight = fields.Float("Peso", readonly=True)
    volume = fields.Float("Volumen", readonly=True)
    order_id = fields.Many2one("purchase.order", "Orden", readonly=True)
    untaxed_total = fields.Float("Total sin impuestos", readonly=True)
    qty_ordered = fields.Float("Cant Ordenada", readonly=True)
    qty_received = fields.Float("Cant recibida", readonly=True)
    qty_billed = fields.Float("Cant Facturado", readonly=True)
    qty_to_be_billed = fields.Float("Cant para facturar", readonly=True)
    cost_center = fields.Many2one("account.analytic.account", "Centro de costo", readonly=True)
    payment_state = fields.Selection(
        [
            ("no_bill", "No facturado"),
            ("not_paid", "No pagado"),
            ("partial_paid", "Parcialmente pagado"),
            ("fully_paid", "Pago completo"),
            ("overdue", "Pago atrasado"),
        ],
        string="Estado de pagos",
        default="no_bill",
        copy=False,
        readonly=True,
        help="Estado de pagos",
    )
    # amount_due = fields.Float('Monto adeudado')
    invoice_status = fields.Selection(
        [
            ("no", "Nada para facturar"),
            ("to invoice", "Para facturar"),
            ("invoiced", "Totalmente facturado"),
        ],
        string="Estado de facturación",
        default="no",
        readonly=True,
    )
    description_line = fields.Char("Descripción")
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
    journal_id = fields.Many2one("account.journal", string="Diario de pago", readonly=True)
    fortnight_pay = fields.Selection(
        [
            ("1", "Q1"),
            ("2", "Q2"),
        ],
        string="Quincena de pago",
    )

    @property
    def _table_query(self):
        """Report needs to be dynamic to take into account multi-company selected + multi-currency rates"""
        return "%s %s %s %s" % (self._select(), self._from(), self._where(), self._group_by())

    def _select(self):
        select_str = """
                SELECT
                    po.id as order_id,
                    min(l.id) as id,
                    po.date_order as date_order,
                    po.state,
                    po.date_approve,
                    po.dest_address_id,
                    po.partner_id as partner_id,
                    po.user_id as user_id,
                    po.company_id as company_id,
                    po.fiscal_position_id as fiscal_position_id,
                    l.product_id,
                    p.product_tmpl_id,
                    t.categ_id as category_id,
                    c.currency_id,
                    t.uom_id as product_uom,
                    extract(epoch from age(po.date_approve,po.date_order))/(24*60*60)::decimal(16,2) as delay,
                    extract(epoch from age(l.date_planned,po.date_order))/(24*60*60)::decimal(16,2) as delay_pass,
                    count(*) as nbr_lines,
                    sum(l.price_total / COALESCE(po.currency_rate, 1.0))::decimal(16,2) * currency_table.rate as price_total,
                    (sum(l.product_qty * l.price_unit / COALESCE(po.currency_rate, 1.0))/NULLIF(sum(l.product_qty/line_uom.factor*product_uom.factor),0.0))::decimal(16,2) * currency_table.rate as price_average,
                    partner.country_id as country_id,
                    partner.trade_name as trade_name,
                    partner.commercial_partner_id as commercial_partner_id,
                    analytic_account.id as account_analytic_id,
                    po.project_id as cost_center,
                    po.payment_state as payment_state,
                    po.invoice_status as invoice_status,
                    po.payment_type as payment_type,
                    po.journal_id as journal_id,
                    po.fortnight_pay as fortnight_pay,
                    l.name as description_line,
                    sum(p.weight * l.product_qty/line_uom.factor*product_uom.factor) as weight,
                    sum(p.volume * l.product_qty/line_uom.factor*product_uom.factor) as volume,
                    sum(l.price_subtotal / COALESCE(po.currency_rate, 1.0))::decimal(16,2) * currency_table.rate as untaxed_total,
                    sum(l.product_qty / line_uom.factor * product_uom.factor) as qty_ordered,
                    sum(l.qty_received / line_uom.factor * product_uom.factor) as qty_received,
                    sum(l.qty_invoiced / line_uom.factor * product_uom.factor) as qty_billed,
                    case when t.purchase_method = 'purchase' 
                         then sum(l.product_qty / line_uom.factor * product_uom.factor) - sum(l.qty_invoiced / line_uom.factor * product_uom.factor)
                         else sum(l.qty_received / line_uom.factor * product_uom.factor) - sum(l.qty_invoiced / line_uom.factor * product_uom.factor)
                    end as qty_to_be_billed
        """
        return select_str

    def _from(self):
        from_str = """
            FROM
            purchase_order_line l
                join purchase_order po on (l.order_id=po.id)
                join res_partner partner on po.partner_id = partner.id
                    left join product_product p on (l.product_id=p.id)
                        left join product_template t on (p.product_tmpl_id=t.id)
                left join res_company C ON C.id = po.company_id
                left join uom_uom line_uom on (line_uom.id=l.product_uom)
                left join uom_uom product_uom on (product_uom.id=t.uom_id)
                left join account_analytic_account analytic_account on (l.account_analytic_id = analytic_account.id)
                left join {currency_table} ON currency_table.company_id = po.company_id
        """.format(
            currency_table=self.env["res.currency"]._get_query_currency_table(
                {"multi_company": True, "date": {"date_to": fields.Date.today()}}
            ),
        )
        return from_str

    def _where(self):
        return """
            WHERE
                l.display_type IS NULL
        """

    def _group_by(self):
        group_by_str = """
            GROUP BY
                po.company_id,
                po.user_id,
                po.partner_id,
                line_uom.factor,
                c.currency_id,
                l.price_unit,
                po.date_approve,
                l.date_planned,
                l.product_uom,
                po.dest_address_id,
                po.fiscal_position_id,
                l.product_id,
                p.product_tmpl_id,
                t.categ_id,
                po.date_order,
                po.state,
                line_uom.uom_type,
                line_uom.category_id,
                t.uom_id,
                t.purchase_method,
                line_uom.id,
                product_uom.factor,
                partner.country_id,
                partner.commercial_partner_id,
                partner.trade_name,
                analytic_account.id,
                po.payment_state,
                po.invoice_status,
                po.payment_type,
                po.journal_id,
                po.fortnight_pay,
                l.name,
                po.id,
                currency_table.rate
        """
        return group_by_str

    @api.model
    def read_group(self, domain, fields, groupby, offset=0, limit=None, orderby=False, lazy=True):
        """This is a hack to allow us to correctly calculate the average of PO specific date values since
        the normal report query result will duplicate PO values across its PO lines during joins and
        lead to incorrect aggregation values.

        Only the AVG operator is supported for avg_days_to_purchase.
        """
        avg_days_to_purchase = next(
            (field for field in fields if re.search(r"\bavg_days_to_purchase\b", field)), False
        )

        if avg_days_to_purchase:
            fields.remove(avg_days_to_purchase)
            if any(field.split(":")[1].split("(")[0] != "avg" for field in [avg_days_to_purchase] if field):
                raise UserError(
                    "Value: 'avg_days_to_purchase' should only be used to show an average. If you are seeing this message then it is being accessed incorrectly."
                )

        if "price_average:avg" in fields:
            fields.extend(["aggregated_qty_ordered:array_agg(qty_ordered)"])
            fields.extend(["aggregated_price_average:array_agg(price_average)"])

        res = []
        if fields:
            res = super(PurchaseReportSanmex, self).read_group(
                domain, fields, groupby, offset=offset, limit=limit, orderby=orderby, lazy=lazy
            )

        if "price_average:avg" in fields:
            qties = "aggregated_qty_ordered"
            special_field = "aggregated_price_average"
            for data in res:
                if data[special_field] and data[qties]:
                    total_unit_cost = sum(
                        float(value) * float(qty)
                        for value, qty in zip(data[special_field], data[qties])
                        if qty and value
                    )
                    total_qty_ordered = sum(float(qty) for qty in data[qties] if qty)
                    data["price_average"] = (total_unit_cost / total_qty_ordered) if total_qty_ordered else 0
                del data[special_field]
                del data[qties]
        if not res and avg_days_to_purchase:
            res = [{}]

        if avg_days_to_purchase:
            self.check_access_rights("read")
            query = """ SELECT AVG(days_to_purchase.po_days_to_purchase)::decimal(16,2) AS avg_days_to_purchase
                          FROM (
                              SELECT extract(epoch from age(po.date_approve,po.create_date))/(24*60*60) AS po_days_to_purchase
                              FROM purchase_order po
                              WHERE po.id IN (
                                  SELECT "purchase_report_sanmex"."order_id" FROM %s WHERE %s)
                              ) AS days_to_purchase
                    """

            subdomain = AND([domain, [("company_id", "=", self.env.company.id), ("date_approve", "!=", False)]])
            subtables, subwhere, subparams = expression(subdomain, self).query.get_sql()

            self.env.cr.execute(query % (subtables, subwhere), subparams)
            res[0].update(
                {
                    "__count": 1,
                    avg_days_to_purchase.split(":")[0]: self.env.cr.fetchall()[0][0],
                }
            )
        return res
