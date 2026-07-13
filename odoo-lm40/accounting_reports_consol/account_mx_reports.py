# -*- encoding: utf-8 -*-
###########################################################################
#    Module Writen to OpenERP, Open Source Management Solution
#
#    Copyright (c) 2014 Argil Consulting - http://www.argil.mx
############################################################################
#    Coded by: Israel Cruz Argil (israel.cruz@argil.mx)
############################################################################
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Affero General Public License as
#    published by the Free Software Foundation, either version 3 of the
#    License, or (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Affero General Public License for more details.
#
#    You should have received a copy of the GNU Affero General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################


from odoo.tools.float_utils import float_round as round
from odoo.tools import DEFAULT_SERVER_DATETIME_FORMAT
from odoo.exceptions import UserError, ValidationError
from odoo import api, fields, models, _
import odoo.addons.decimal_precision as dp

class AccountMoveLine(models.Model):
    _inherit = "account.move.line"


    @api.depends('move_id.state')
    def _compute_state(self):
        for record in self.filtered('move_id'):
            record.state = record.move_id.state
            #record.state2= record.move_id.state

    state = fields.Char(compute="_compute_state", help="State of the parent account.move", store=True)
    #state2 = fields.Char(compute="_compute_state", help="State of the parent account.move", store=True)

class AccountMonthlyBalanceWizard(models.TransientModel):
    _name = "account.monthly_balance_wizard"
    _description = "Generador de Balanza de Comprobacion"


    @api.model
    def _get_period_id(self):
        period = self.env['account.period'].search([('date_start', '<=', fields.Date.today()), ('date_stop', '>=', fields.Date.today()), ('company_id', '=', self.env.user.company_id.id)], limit=1)
        self.period_id = period and period[0] or False
        
    
    chart_account_id  = fields.Many2one('account.account', string='Chart of Account', 
                                        help='Select Charts of Accounts', required=True, 
                                        domain = [('parent_id','=',False)], 
                                        default=lambda self: self.env['account.account'].search([('parent_id','=',False),('company_id','=',self.env.user.company_id.id)], limit=1))
    company_id        = fields.Many2one('res.company', string='Company', change_default=True,
                            required=True, readonly=True,
                            default = lambda self: self.env.user.company_id)
    
    period_id          = fields.Many2one('account.period', string = 'Periodo', required=True,
                                        default=lambda self: self.env['account.period'].search([('date_start', '<=', fields.Date.today()), ('date_stop', '>=', fields.Date.today()), ('company_id', '=', self.env.user.company_id.id),('special','=',False)], limit=1))
    partner_breakdown  = fields.Boolean('Desglosar Empresas', default=False)
    output             = fields.Selection([
                                            ('list_view','Vista Lista'), 
                                            ('pdf','PDF'), 
                                        ], string = 'Salida',required=True, default='list_view')
    
        


class AccountMonthlyBalanceHeader(models.Model):
    _name = "account.monthly_balance_header"
    _description = "Header Balanza Mensual"

    create_uid  = fields.Many2one('res.users', string='Usuario', readonly=True)
    period_name = fields.Char(string='Periodo', size=64, readonly=True)
    date        = fields.Date(string='Fecha', readonly=True)
    line_ids    = fields.One2many('account.monthly_balance', 'header_id', string='Lines')
    
    _order = 'period_name asc'


class AccountMonthlyBalance(models.Model):
    _name = "account.monthly_balance"
    _description = "Account Chart Monthly Balance"


    header_id       = fields.Many2one('account.monthly_balance_header', string='Header', readonly=True)
    company_name    = fields.Char(string='Compañia', size=64, readonly=True)
    period_name     = fields.Char(string='Periodo', size=64, readonly=True)                
    period_id       = fields.Many2one('account.period', string='Periodo', readonly=True)
    account_id      = fields.Many2one('account.account', string='Cuenta Contable', readonly=True)
    account_code    = fields.Char(string='Codigo', size=64, readonly=True)
    account_name    = fields.Char(string='Descripcion', size=250, readonly=True)
    account_level   = fields.Integer(string='Nivel', readonly=True)
    account_type    = fields.Char(string='Tipo', size=64, readonly=True)
    account_internal_type = fields.Char(string='Tipo Interno', size=64, readonly=True)
    account_nature  = fields.Char(string='Naturaleza', size=64, readonly=True)
    account_sign    = fields.Integer(string='Signo', readonly=True)
    initial_balance = fields.Float(string='Saldo Inicial', readonly=True, digits=dp.get_precision('Account'))
    debit           = fields.Float(string='Cargos', readonly=True, digits=dp.get_precision('Account'))
    credit          = fields.Float(string='Abonos', readonly=True, digits=dp.get_precision('Account'))
    balance         = fields.Float(string='Saldo del Periodo', readonly=True, digits=dp.get_precision('Account'))
    ending_balance  = fields.Float(string='Saldo Acumulado', readonly=True, digits=dp.get_precision('Account'))
    moves           = fields.Boolean(string='Con Movimientos', readonly=True)
    create_uid      = fields.Many2one('res.users', string='Created by', readonly=True)
    partner_id      = fields.Many2one('res.partner', string='Empresa', readonly=True, required=False)
    partner_name    = fields.Char(string='Empresa', size=128, readonly=True, required=False)
    order_code      = fields.Char(string='Codigo orden', size=64, readonly=True)
    
    _order = 'order_code, account_level, partner_name asc'

                    
class AccountAccountLinesHeader(models.Model):
    _name = "account.account_lines_header"

    create_uid      = fields.Many2one('res.users', string='Usuario', readonly=True)
    account_id      = fields.Many2one('account.account', string='Cuenta Contable', readonly=True)
    period_id_start = fields.Many2one('account.period', string='Periodo Inicial', readonly=True)
    period_id_end   = fields.Many2one('account.period', string='Periodo Final', readonly=True)
    partner_id      = fields.Many2one('res.partner', string='Empresa', readonly=True)
    product_id      = fields.Many2one('product.product', 'Producto', readonly=True)
    debit_sum       = fields.Float(string='Cargos', readonly=True, digits=dp.get_precision('Account'))
    credit_sum      = fields.Float(string='Abonos', readonly=True, digits=dp.get_precision('Account'))
    line_ids        = fields.One2many('account.account_lines', 'header_id', string='Lines')



class AccountAccountLines(models.Model):
    _name = "account.account_lines"
    _description = "Auxiliar de Cuentas"


    header_id         = fields.Many2one('account.account_lines_header', string='Header', readonly=True, ondelete='cascade')
    name              = fields.Char(string='Concepto Partida', size=256, readonly=True)
    ref               = fields.Char(string='Referencia Partida', size=256, readonly=True)
    move_id           = fields.Many2one('account.move', string='Póliza', readonly=True)
    user_id           = fields.Many2one('res.users', string='Usuario', readonly=True)
    journal_id        = fields.Many2one('account.journal', string='Diario', readonly=True)
    period_id         = fields.Many2one('account.period', string='Periodo', readonly=True)
    fiscalyear_id     = fields.Many2one('account.fiscal', string='Periodo Anual', 
                                        related='period_id.fiscalyear_id', store=False, readonly=True)
    account_id        = fields.Many2one('account.account', string='Cuenta Contable', readonly=True)
    account_type_id   = fields.Many2one('account.account.type', string='Tipo Cuenta', readonly=True)
    move_date         = fields.Date(string='Fecha Póliza', readonly=True)
    move_name         = fields.Char(string='Póliza No.', size=256, readonly=True)
    move_ref          = fields.Char(string='Referencia Póliza', size=256, readonly=True)
    period_name       = fields.Char(string='xPeriodo Mensual', size=256, readonly=True)
    fiscalyear_name   = fields.Char(string='xPeriodo Anual', size=256, readonly=True)
    account_code      = fields.Char(string='Codigo Cuenta', size=256, readonly=True)
    account_name      = fields.Char(string='Descripcion Cuenta', size=256, readonly=True)
    account_level     = fields.Integer(string='Nivel', readonly=True)
    account_type      = fields.Char(string='xTipo Cuenta', size=256, readonly=True)
    account_sign      = fields.Integer(string='Signo', readonly=True)
    journal_name      = fields.Char(string='xDiario', size=256, readonly=True)
    initial_balance   = fields.Float(string='Saldo Inicial', readonly=True, digits=dp.get_precision('Account'))
    debit             = fields.Float(string='Cargos', readonly=True, digits=dp.get_precision('Account'))
    credit            = fields.Float(string='Abonos', readonly=True, digits=dp.get_precision('Account'))
    ending_balance    = fields.Float(string='Saldo Final', readonly=True, digits=dp.get_precision('Account'))
    partner_id        = fields.Many2one('res.partner', string='Empresa', readonly=True)
    product_id        = fields.Many2one('product.product', string='Producto', readonly=True)
    qty               = fields.Float(string='Cantidad', readonly=True)
    sequence          = fields.Integer(string='Seq', readonly=True)
    amount_currency   = fields.Float(string='Monto M.E.', readonly=True, help="Monto en Moneda Extranjera", digits=dp.get_precision('Account'))
    currency_id       = fields.Many2one('res.currency', string='Moneda', readonly=True)
    
    _order = 'sequence, period_name, move_date, account_code'



class AccountAccountLinesWizard(models.TransientModel):
    _name = "account.account_lines_wizard"
    _description = "Auxiliar de Cuentas"

    company_id      = fields.Many2one('res.company', string='Company', readonly=True,
                                     default = lambda self: self.env.user.company_id)
    fiscalyear_id   = fields.Many2one('account.fiscal', string='Periodo Anual',
                                     default=lambda self: self.env['account.fiscal'].search([('date_start', '<=', fields.Date.today()), ('date_stop', '>=', fields.Date.today()), ('company_id', '=', self.env.user.company_id.id)], limit=1))
    period_id_start = fields.Many2one('account.period', string='Periodo Inicial',
                                     default=lambda self: self.env['account.period'].search([('date_start', '<=', fields.Date.today()), ('date_stop', '>=', fields.Date.today()), ('company_id', '=', self.env.user.company_id.id),('special','=',False)], limit=1))
    period_id_stop  = fields.Many2one('account.period', string='Periodo Final',
                                     default=lambda self: self.env['account.period'].search([('date_start', '<=', fields.Date.today()), ('date_stop', '>=', fields.Date.today()), ('company_id', '=', self.env.user.company_id.id),('special','=',False)], limit=1))
    account_id      = fields.Many2one('account.account', string='Cuenta Contable')
    partner_id      = fields.Many2one('res.partner', string='Empresa')
    product_id      = fields.Many2one('product.product', string='Producto')
    output          = fields.Selection([
                                    ('list_view','Vista Lista'), 
                                    ('pdf','PDF'), 
                                ], string='Salida',required=True, default='list_view')



# Configurador de reportes basados en la Balanza de Comprobacion Mensual
#
class AccountMXReportDefinition(models.Model):
    _name = "account.mx_report_definition"
    _description = "Definición de Reportes basados en Balanza de Comprobación"

    #@api.model
    def name_get(self):
        reads = self.read(['name','parent_id'])
        res = []
        for record in reads:
            name = record['name']
            if record['parent_id']:
                name = record['parent_id'][1]+' / '+name
            res.append((record['id'], name))
        return res

    #@api.model
    def _name_get_fnc(self):
        res = self.name_get()
        return dict(res)

    
    name              = fields.Char(string='Nombre', size=64, required=True)
    complete_name     = fields.Char(string='Nombre Completo', size=300, store=True, compute='_name_get_fnc', method=True)
    parent_id         = fields.Many2one('account.mx_report_definition',string='Parent Category', index=True)
    child_id          = fields.One2many('account.mx_report_definition', 'parent_id', string='Childs')
    sequence          = fields.Integer(string='Secuencia', help="Determina el orden en que se muestran los registros...")
    type              = fields.Selection([
                                        ('sum','Acumula'), 
                                        ('detail','Detalle'), 
                                    ], string='Tipo',required=True, defaut='sum')
    sign              = fields.Selection([
                                    ('positive', 'Positivo'), 
                                    ('negative', 'Negativo'), 
                                ], string='Signo',required=True, default='positive')
    print_group_sum   = fields.Boolean(string='Titulo de Grupo', help="Indica si se imprime el título del grupo de reporte...")
    print_report_sum  = fields.Boolean(string='Suma Final', help="Indica si se imprime la sumatoria total del reporte...")
    internal_group    = fields.Char(string='Grupo Interno', size=64, required=True)
    initial_balance   = fields.Boolean(string='Saldo Inicial Acum.')
    debit_and_credit  = fields.Boolean(string='Cargos y Abonos')
    ending_balance    = fields.Boolean(string='Saldo Final Acum.')
    debit_credit_ending_balance= fields.Boolean(string='Saldo Final Periodo')
    account_ids       = fields.Many2many('account.account', 'account_account_mx_reports_rel', 'mx_report_definition_id', 'account_id', string='Accounts')
    report_id         = fields.Many2one('account.mx_report_definition',string='Usar Reporte')
    report_id_use_resume = fields.Boolean(string='Solo Resultado', help="Si activa este campo solo se obtendra el resultado del reporte, de lo contrario se obtendra el detalle de las cuentas y/o subreportes incluidos.")
    report_id_account = fields.Char(string='Cuenta', size=64, help="Indique el numero de cuenta a mostrar en el reporte")
    report_id_label   = fields.Char(string='Descripcion', size=64, help="Indique la descripcion de la cuenta a mostrar en el reporte")
    report_id_show_result= fields.Boolean(string='Mostrar Resultado', help="Active esta casilla si desea que se muestre el resultado del subreporte")
    active            = fields.Boolean(string='Activo', default=True)
    account_entries   = fields.Boolean(string='Desglosar Movimientos')
    
    _order = 'sequence'


    @api.constrains('parent_id')
    def _check_parent_id_recursion(self):
        if not self._check_recursion():
            raise ValidationError(_('Error ! You cannot create recursive reports.'))
        return True
    
    @api.constrains('report_id')
    def _check_report_id_recursion(self):
        if not self._check_recursion():
            raise ValidationError(_('Error ! You cannot create recursive reports.'))
        return True    
    

class AccountMXReportDataWizard(models.TransientModel):
    _name = "account.mx_report_data_wizard"
    _description = "Generador de Reporte Financiero"

    report_id    = fields.Many2one('account.mx_report_definition', string='Reporte Contable', required=True)
    period_id    = fields.Many2one('account.period', string='Periodo', required=True)
    report_type  = fields.Selection([('xls','XLS'),('pdf','PDF')
                                        ], string='Tipo', default='pdf')
    print_detail = fields.Boolean(string='Imprimir Detalle', help='Permite Imprimir en el Reporte el detalle de Movimientos.')
