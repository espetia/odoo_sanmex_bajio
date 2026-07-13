# -*- coding: utf-8 -*-
###########################################################################

from odoo import models, fields, api, _
from odoo.exceptions import UserError


class stock_location(models.Model):
    _inherit = "stock.location"

    change_std_price_account_id = fields.Many2one('account.account', string='Change Standard Price Account', 
                                                    domain=[('internal_type', '=', 'other')],
                            help="This account will be used when changing Product Standard Price, if this account is not set then default product accounts will be used.")
    accout_local_cost = fields.Many2one('account.account', string='Cuenta de salida de stock', domain=[('internal_type', '=', 'other')])
    account_cost_inventory = fields.Many2one('account.account', string='Cuenta de Costo de Venta para Ajustes y Desecho', domain=[('internal_type', '=', 'other')])
 
