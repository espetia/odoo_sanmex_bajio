# -*- coding: utf-8 -*-

from odoo import models, fields, api


class RegistroPatronal(models.Model):
    _name = "registro.patronal"

    name = fields.Char(string='Registro patronal')
    company_id = fields.Many2one(
        comodel_name='res.company',
        string='Compañía',
        default=lambda self: self.env.company.id,
    )
