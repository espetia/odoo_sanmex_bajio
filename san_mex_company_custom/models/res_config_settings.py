# -*- coding: utf-8 -*-

from odoo import models, fields

class ResCompany(models.Model):
    _inherit = 'res.company'

    ppd_notification_user_ids = fields.Many2many(
        'res.users',
        'company_ppd_notification_users_rel',
        'company_id',
        'user_id',
        string='PPD Notification Users'
    )


class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    ppd_notification_user_ids = fields.Many2many(
        related='company_id.ppd_notification_user_ids',
        readonly=False,
        string='PPD Notification Users'
    )
