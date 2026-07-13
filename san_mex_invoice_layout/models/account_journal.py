# -*- coding: utf-8 -*-
from odoo import models, fields

class AccountJournal(models.Model):
    _inherit = 'account.journal'

    bank = fields.Char(string='Bank')
    account_number = fields.Char(string='Account Number')
    key_account = fields.Char(string='Key Account')
    card_number = fields.Char(string='Card Number')
