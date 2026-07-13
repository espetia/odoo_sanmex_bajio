# -*- coding: utf-8 -*-

from odoo import models, fields, api


class CreditoInfonavit(models.Model):
    _inherit = 'credito.infonavit'

    def enviar_data(self):
        contrato_id = self.employee_id.contract_ids[0] if self.employee_id.contract_ids else False
        if contrato_id:
            contrato_id.infonavit_fijo = 0
            contrato_id.infonavit_vsm = 0
            contrato_id.infonavit_porc = 0
            if self.tipo_de_descuento == '1':
                contrato_id.infonavit_porc = self.valor_descuento
            elif self.tipo_de_descuento == '2':
                contrato_id.infonavit_fijo = self.valor_descuento
            elif self.tipo_de_descuento == '3':
                contrato_id.infonavit_vsm = self.valor_descuento