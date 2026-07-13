# -*- coding: utf-8 -*-
#

from odoo import api, fields, models, _
import logging
_logger = logging.getLogger(__name__)


class AccountAccountType(models.Model):
    _inherit = "account.account.type"

    type = fields.Selection(selection_add=[('view', 'Vista'),
                             ('consolidation', 'Consolidación'),
                             #('other', 'Regular'),
                             #('receivable', 'Receivable'),
                             #('liquidity', 'Liquidity'),
                             #('payable', 'Payable'),
                            ], ondelete={'view': 'set default', 'consolidation': 'set default'})


class AccountAccount(models.Model):
    _inherit = "account.account"

    #@api.model
    @api.depends('parent_id')
    def _get_level(self):
        #self.ensure_one()
        level = 0
        parent = self.parent_id or False
        while parent:
            level += 1
            parent = parent.parent_id or False
        self.level = level

    #@api.model
    @api.depends('child_parent_ids')
    def _get_child_ids(self):
        self.ensure_one()
        result = []
        if self.child_parent_ids:
            for record in self.child_parent_ids:
                result.append(record.id)            

        if self.child_consol_ids:
            for acc in self.child_consol_ids:
                if acc.id not in result:
                    result.append(acc.id)
        self.child_id = result
        

    @api.model
    def _get_children_and_consol(self, ids=[]):
        #this function search for all the children and all consolidated children (recursively) of the given account ids
        ids = list(ids)
        res = []
        record = self.search([('parent_id', 'child_of', ids)])
        ids3 = []
        for rec in record:
            res.append(rec.id)
            for child in rec.child_consol_ids:
                res.append(child.id)
        
        return res

    @api.model
    def __compute_account(self):
        query=''
        context = self._context.copy()        
        context2 = context.copy()
        periods = context.get('periods', False)
        
        if periods:
            subquery = """select p2.id from account_period p2
                            where p2.name2 < (select min(name2) from account_period p1
                                              where id in (%s));
                """ % (str(periods).replace('[','').replace(']',''))
            self._cr.execute( subquery )
            period_ids = [period_id[0] for period_id in self._cr.fetchall() ]
            res2 = {}
            if period_ids:
                context2.update({'periods': period_ids, 'period_id': False})
                res2 = self.with_context(context2).__compute()
        res1 = self.__compute()
        self.initial_balance = (periods and 'balance' in res2) and res2['balance'] or 0.0
        self.balance_all = ('balance' in res1 and res1['balance'] or 0.0) + ((periods and 'balance' in res2) and res2['balance'] or 0.0) 
        self.debit  = 'debit' in res1 and res1['debit'] or 0.0
        self.credit = 'credit' in res1 and res1['credit'] or 0.0
        self.balance= 'balance' in res1 and res1['balance'] or 0.0

    @api.onchange('sign')
    def _compute_naturaleza(self): 
        for x in self:   
            if x.sign == 'debit':
                x.sing_1 = 1
            else:
                x.sing_1 = -1
    
    initial_balance = fields.Monetary(compute=__compute_account, string='Initial Balance')
    balance_all     = fields.Monetary(compute=__compute_account, string='Balance All')
    balance               = fields.Monetary(compute=__compute_account, string='Balance')
    credit                = fields.Monetary(compute=__compute_account, string='Credit')
    debit                 = fields.Monetary(compute=__compute_account, string='Debit')

    parent_id = fields.Many2one('account.account', string='Padre', required=False, index=True)
    sign = fields.Selection([
        ('debit', 'Debitable'), 
        ('credit', 'Creditable') 
        ], string='Naturaleza de cuenta', required=True, default='debit')
    sing_1 = fields.Integer(string='Naturaleza', default=1)
    partner_breakdown = fields.Boolean(index=True, default=False, string='Desglosar Empresas en Balanza', 
                                       help= 'Si activa esta casilla se desglosará en la Balanza de Comprobación las empresas que conforman los cargos / abonos y saldos de esta cuenta')

    sat_code_id = fields.Many2one('sat.account.code', 'Código Agrupador SAT')
    xml_report = fields.Boolean('Considerar para Contabilidad Electrónica')
    account_bank = fields.Char('No. de Cuenta')
    bank_id = fields.Many2one('res.bank', 'Banco')
    currency_id = fields.Many2one('res.currency', 'Moneda')   
    first_period_id = fields.Many2one('account.period', 'Primer periodo reportado', help='Periodo en que la cuenta fue reportada por primera vez ante el SAT. Ningún XML generado con un periodo anterior incluirá esta cuenta.')
    child_consol_ids  = fields.Many2many('account.account', 'account_account_consol_rel', 'child_id', 'parent_id', string='Consolidated Children')
    in_debt = fields.Boolean(string='Deudora', default=True)
    in_cred = fields.Boolean(string='Acreedora')
    level = fields.Integer(string='Level', store=True, readonly=True, compute=_get_level, method=True)
    child_id = fields.Many2many('account.account', compute=_get_child_ids,  string="Child Accounts", store=False)
    child_parent_ids  = fields.One2many('account.account','parent_id', string='Children')
    
    @api.onchange('in_debt')
    def on_change_debt(self):
        self.in_cred = not self.in_debt
        
    @api.onchange('in_cred')
    def on_change_cred(self):
        self.in_debt = not self.in_cred    
        

    @api.model
    def launch_period_chooser(self):
        if not len(self._context['active_ids']):
            raise UserError(_('No ha seleccionado cuentas contables para procesar.'))
        return {
            'type': 'ir.actions.act_window',
             'res_model': 'period.chooser',
             'view_mode': 'form',
             'view_type': 'form',
             'target': 'new',
             'name': 'Contabilidad Electrónica - Catálogo de cuentas',
             'context': {'active_ids': self._context['active_ids']}
            }

class period_chooser(models.TransientModel):
    _name = 'period.chooser'
    
    period_id = fields.Many2one('account.period', string='Periodo a generar', required=True)

    @api.model
    def generate_xml(self):
        wizard_vals = { 'xml_target': 'accounts_catalog',
                        'month': self.period_id.date_start[5:7],
                        'year': int(self.period_id.date_start[0:4])}
        wizId = self.env['files.generator.wizard'].create(wizard_vals)
        return wizId.process_file(account_ids=self._context['active_ids'])
