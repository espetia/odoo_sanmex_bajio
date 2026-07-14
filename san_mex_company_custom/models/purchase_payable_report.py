# -*- coding: utf-8 -*-
from odoo import api, fields, models
from odoo.tools import drop_view_if_exists


class PurchasePayableReport(models.Model):
    _name = 'purchase.payable.report'
    _description = 'Reporte de compras por pagar'
    _auto = False
    _rec_name = 'name'
    _order = 'payment_date desc, id desc'

    # Campos desde Purchase Order
    trade_name = fields.Char(string='Nombre Comercial', readonly=True)
    order_id = fields.Many2one('purchase.order', string='Orden de Compra', readonly=True)

    # Campos desde Purchase Order Line / Order
    product_id = fields.Many2one('product.product', string='Producto', readonly=True)
    name = fields.Text(string='Descripción', readonly=True)
    date_order = fields.Datetime(string='Fecha de Orden', readonly=True)

    price_unit = fields.Monetary(string='Precio Unitario', currency_field='currency_id', readonly=True)
    product_qty = fields.Float(string='Cantidad', readonly=True)
    price_total = fields.Monetary(string='Total', currency_field='currency_id', readonly=True)

    # Campos personalizados de la línea (arrastrados desde la orden)
    payment_date = fields.Date(string='Fecha de Pago', readonly=True)
    # Mes (numérico) derivado de payment_date para permitir filtros por mes
    payment_month = fields.Integer(string='Mes de Pago', readonly=True)
    # Año derivado de payment_date para permitir filtros por año
    payment_year = fields.Integer(string='Año de Pago', readonly=True)
    # Utilizamos Char para evitar dependencia directa de la definición de selección
    payment_type = fields.Char(string='Tipo de Pago', readonly=True)
    internal_note = fields.Text(string='Nota Interna', readonly=True)
    vehicle_id = fields.Many2one('fleet.vehicle', string='Vehículo', readonly=True)
    project_id = fields.Many2one('account.analytic.account', string='Cuenta Analítica', readonly=True)

    state = fields.Char(string='Estado', readonly=True)

    # Soporte monetario
    currency_id = fields.Many2one('res.currency', string='Moneda', readonly=True)
    company_id = fields.Many2one('res.company', string='Compañía', readonly=True)

    # Campos adicionales solicitados desde Purchase Order
    # Usamos Char para evitar dependencias de selección/relaciones en el modelo de vista
    fortnight_pay = fields.Char(string='Quincena de Pago', readonly=True)
    journal_name = fields.Char(string='Diario de Pagos', readonly=True)
    partner_name = fields.Char(string='Proveedor', readonly=True)

    # Claves para agrupar
    journal_id = fields.Many2one('account.journal', string='Diario', readonly=True)
    partner_id = fields.Many2one('res.partner', string='Proveedor', readonly=True)

    # Campo calculado (no almacenado)
    iva_amount = fields.Monetary(
        string='Impuestos',
        currency_field='currency_id',
        compute='_compute_iva_amount',
        store=False,
        readonly=True,
    )

    @api.depends('price_unit', 'product_qty')
    def _compute_iva_amount(self):
        """Calcula el monto de impuestos usando los métodos nativos de impuestos.
        Reglas:
        - Si la línea no tiene impuestos (taxes_id vacío), el impuesto es 0.0.
        - Si tiene impuestos, se calcula como total_included - total_excluded de compute_all.
        Se basa en la línea original de compra (purchase.order.line) enlazada por el ID de la vista.
        """
        PurchaseLine = self.env['purchase.order.line']
        for rec in self:
            # El ID del registro en esta vista coincide con el ID de purchase.order.line
            pol = PurchaseLine.browse(rec.id)
            if not (pol and pol.exists()):
                rec.iva_amount = 0.0
                continue

            taxes = pol.taxes_id
            if not taxes:
                # Sin impuestos configurados en la línea → impuesto = 0
                rec.iva_amount = 0.0
                continue

            currency = pol.order_id.currency_id
            partner = pol.order_id.partner_id
            product = pol.product_id
            # compute_all maneja impuestos incluidos/excluidos
            res = taxes.compute_all(
                price_unit=pol.price_unit,
                currency=currency,
                quantity=pol.product_qty,
                product=product,
                partner=partner,
            )
            rec.iva_amount = res.get('total_included', 0.0) - res.get('total_excluded', 0.0)

    def init(self):
        # Crear o reemplazar la vista SQL
        cr = self.env.cr
        drop_view_if_exists(cr, self._table)
        cr.execute(
            f"""
            CREATE OR REPLACE VIEW {self._table} AS (
                SELECT
                    pol.id                   AS id,
                    rp.trade_name            AS trade_name,
                    po.id                    AS order_id,
                    pol.product_id           AS product_id,
                    pol.name                 AS name,
                    po.date_order            AS date_order,
                    pol.price_unit           AS price_unit,
                    pol.product_qty          AS product_qty,
                    pol.price_total          AS price_total,
                    po.payment_date          AS payment_date,
                    EXTRACT(MONTH FROM po.payment_date)::int AS payment_month,
                    EXTRACT(YEAR FROM po.payment_date)::int  AS payment_year,
                    po.payment_type          AS payment_type,
                    po.internal_note         AS internal_note,
                    pol.vehicle_id            AS vehicle_id,
                    po.project_id            AS project_id,
                    po.state                 AS state,
                    po.currency_id           AS currency_id,
                    po.company_id            AS company_id,
                    CASE
                        WHEN po.fortnight_pay IS NULL THEN NULL
                        ELSE 'Q' || po.fortnight_pay::text
                    END                      AS fortnight_pay,
                    aj.name                  AS journal_name,
                    rp.name                  AS partner_name,
                    po.journal_id            AS journal_id,
                    po.partner_id            AS partner_id
                FROM purchase_order_line pol
                JOIN purchase_order po ON pol.order_id = po.id
                JOIN res_partner rp ON po.partner_id = rp.id
                LEFT JOIN account_journal aj ON po.journal_id = aj.id
                WHERE pol.invoice_status != 'invoiced'
                  AND po.state = 'purchase'
                  AND po.payment_date >= DATE '2023-01-01'
                  AND po.exceptional_purchase_order IS NOT TRUE
            )
            """
        )
