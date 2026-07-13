# -*- coding: utf-8 -*-
import logging

from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError

_logger = logging.getLogger(__name__)


class ProductTemplate(models.Model):
    _inherit = 'product.template'

    is_resource_rent = fields.Boolean('Recurso para Renta')
    is_resource_sanitary = fields.Boolean('Es sanitario')
    type_product_rent = fields.Selection(
        string=_('Tipo de producto'),
        selection=[
            ('obra', 'Sanitario de obra'),
            ('evento', 'Sanitario de evento'),
        ],
    )
    stock_house_id = fields.Many2one('stock.warehouse', string='Almacén')