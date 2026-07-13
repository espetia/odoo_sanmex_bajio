from odoo import api, fields, models, _, tools

from odoo.exceptions import UserError, RedirectWarning, ValidationError
from odoo.osv import osv, expression
import logging
_logger = logging.getLogger(__name__)
import re



class Employee(models.Model):
    _inherit = "hr.employee"

    numlicencia = fields.Char(string='Numero de liciencia')
    rfcfigura = fields.Char(string='RFC')
    tipofigura = fields.Many2one('c_figuratransporte', string='Tipo Figura')
    tipofigura_is = fields.Boolean('Es chofer')
