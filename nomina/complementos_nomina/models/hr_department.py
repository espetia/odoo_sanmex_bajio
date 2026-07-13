# -*- coding: utf-8 -*-

from odoo import api, fields, models
from odoo.exceptions import UserError


class HrDepartment(models.Model):
    _inherit = 'hr.department'

    @api.model
    def create(self, vals):
        if 'name' in vals:
            existe = self.search([
                ('name', 'ilike', vals['name'])
            ])
            if existe:
                raise UserError('Ya existe un departamento con el nombre: {0}'.format(vals['name']))
        return super(HrDepartment, self).create(vals)

    def write(self, vals):
        if 'name' in vals:
            existe = self.search([
                ('name', 'ilike', vals['name'])
            ])
            if existe:
                raise UserError('Ya existe un departamento con el nombre: {0}'.format(vals['name']))
        return super(HrDepartment, self).write(vals)
