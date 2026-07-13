# -*- coding: utf-8 -*-

from datetime import datetime

from odoo import api, fields, models


class Contract(models.Model):
    _inherit = "hr.contract"

    @api.depends('date_start')
    def _compute_fch_antiguedad(self):
        for record in self:
            if not record.fch_antiguedad and record.date_start:
                record.write({'fch_antiguedad': record.date_start})
            record.fch_antiguedad_automatico = True

    infonavit_mov_perm = fields.Boolean(string='Infonavit movimiento permanente')
    infonavit_mov_perm_monto = fields.Float(
        string='Monto Infonavit movimiento permanente',
        digits=(12, 4)
    )
    fch_antiguedad = fields.Date(string=u'Fecha antigüedad reconocida')
    fch_antiguedad_automatico = fields.Boolean(compute=_compute_fch_antiguedad)
    transporte = fields.Boolean(string='Transporte')
    transporte_monto = fields.Float(
        string='Monto Transporte',
        digits=(12, 4)
    )
    retroactivo = fields.Boolean(string='Retroactivo')
    retroactivo_monto = fields.Float(
        string='Monto Retroactivo',
        digits=(12, 4)
    )
    seguro_vivienda = fields.Boolean(string='Incluir pago de seguro de vivienda')

    @api.depends('date_start')
    def _compute_antiguedad_anos(self):
        if self.date_start:
            date_start = self.fch_antiguedad
            today = datetime.today().date()
            diff_date = today - date_start
            years = diff_date.days / 365.0
            self.antiguedad_anos = int(years)
