# -*- coding: utf-8 -*-

from odoo import models, api, fields


class GeneraLiquidaciones(models.TransientModel):
    _inherit = 'calculo.liquidaciones'

    tipo_de_baja = fields.Selection([
        ('01', 'Separación voluntaria'),
        ('02', 'Liquidación')
    ])
    employee_id = fields.Many2one(
        string='Empleado',
        domain=[
            '|',
            ('contract_id.state', '=', 'close'),
            ('contract_id.date_end', '!=', False)
        ]
    )

    @api.onchange('employee_id')
    def _onchange_employee_id(self):
        if self.employee_id:
            self.contract_id = self.employee_id.contract_id
            self.fecha_liquidacion = self.employee_id.contract_id.date_end
            self.estructura = self.employee_id.contract_id.struct_id