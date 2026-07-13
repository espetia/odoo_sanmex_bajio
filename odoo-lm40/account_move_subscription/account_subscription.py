# -*- coding: utf-8 -*-
##############################################################################
#
#   Original by Odoo SA
#   Forked by:
#   2016 - Argil Consulting SA de CV
#    (<http://www.argil.mx>)
##############################################################################

from odoo import api, fields, models, _
import odoo.addons.decimal_precision as dp
from odoo.exceptions import UserError
from datetime import datetime
from dateutil.relativedelta import relativedelta
import time
# ---------------------------------------------------------
# Account Entries Models
# ---------------------------------------------------------

class account_model(models.Model):
    _name = "account.model"
    _description = "Account Model for Account Move Subscription"

    name        = fields.Char(string='Nombre del Modelo', required=True, help="This is a model for recurring accounting entries")
    journal_id  = fields.Many2one('account.journal', 'Diario', required=True)
    company_id  = fields.Many2one('res.company', related='journal_id.company_id', string='Compañia', store=True, readonly=True)
    lines_id    = fields.One2many('account.model.line', 'model_id', string='Modelo de pólizas', copy=True)
    legend      = fields.Text(string='Leyenda', readonly=True,
                             default=_('You can specify year, month and date in the name of the model using the following labels:\n\n%(year)s: To Specify Year \n%(month)s: To Specify Month \n%(date)s: Current Date\n\ne.g. My model on %(date)s'))
    notes       = fields.Text(string='Notas')

    
class account_model_line(models.Model):
    _name = "account.model.line"
    _description = "Account Model Entries"

    name        = fields.Char(string='Nombre', required=True)
    sequence    = fields.Integer(string='Sequencia', required=True, help="The sequence field is used to order the resources from lower sequences to higher ones.")
    quantity    = fields.Float(string='Cantidad', digits=dp.get_precision('Account'), help="The optional quantity on entries.")
    debit       = fields.Float(string='Débito', digits=dp.get_precision('Account'))
    credit      = fields.Float(string='Crédito', digits=dp.get_precision('Account'))
    account_id  = fields.Many2one('account.account', string='Cuenta', required=True, ondelete="cascade")
    analytic_account_id = fields.Many2one('account.analytic.account', string='Cuenta Analitica', ondelete="cascade")
    model_id    = fields.Many2one('account.model', string='Modelo', required=True, ondelete="cascade", index=True)
    amount_currency = fields.Float(string='Monto en Moneda', help="The amount expressed in an optional other currency.")
    currency_id = fields.Many2one('res.currency', string='Moneda')
    partner_id  = fields.Many2one('res.partner', string='Cliente')
    date_maturity = fields.Selection([('today','Fecha Hoy'), 
                                      ('partner','Términos de pago cliente')], string='Fecha de Vencimiento', 
                                     help="The maturity date of the generated entries for this model. You can choose between the creation date or the creation date of the entries plus the partner payment terms.")

    _order = 'sequence'
    _sql_constraints = [
        ('credit_debit1', 'CHECK (credit*debit=0)',  'Wrong credit or debit value in model, they must be positive!'),
        ('credit_debit2', 'CHECK (credit+debit>=0)', 'Wrong credit or debit value in model, they must be positive!'),
    ]



# ---------------------------------------------------------
# Account Subscription
# ---------------------------------------------------------


class account_subscription(models.Model):
    _name = "account.subscription"
    _description = "Account Subscription"

    name        = fields.Char(string='Nombre', required=True)
    ref         = fields.Char(string='Referencia')
    model_id    = fields.Many2one('account.model', 'Modelo', required=True)
    date_start  = fields.Date(string='Fecha Inicio', required=True, default=fields.Date.context_today)
    period_total = fields.Integer(string='Número de Periodos', required=True, default=12)
    period_nbr  = fields.Integer(string='Periodo', required=True, default=1)
    period_type = fields.Selection([('day','Dia'),
                                    ('month','Mes'),
                                    ('year','Año')], string='Tipo Periodo', required=True, default='month')
    state       = fields.Selection([('draft','Borrador'),
                                    ('running','En Proceso'),
                                    ('done','Terminado')], string='Status', default='draft',
                                   required=True, readonly=True, copy=False)
    lines_id    = fields.One2many('account.subscription.line', 'subscription_id', 'Subscription Lines', copy=True)


class account_subscription_line(models.Model):
    _name = "account.subscription.line"
    _description = "Account Subscription Line"

    subscription_id = fields.Many2one('account.subscription', string='Subscription', required=True, index=True)
    date            = fields.Date(string='Fecha', required=True)
    move_id         = fields.Many2one('account.move', string='Póliza')

    _rec_name = 'date'


# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:    
