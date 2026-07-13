# -*- coding: utf-8 -*-

from odoo import api, fields, models, _
from odoo.tools import float_compare, float_is_zero
from odoo.exceptions import UserError
from odoo.addons.om_hr_payroll_account.models.hr_payroll_account import HrPayslip

class HrPayslipContaEE(models.Model):
    _inherit = 'hr.payslip'
    
#     @api.multi
    def action_payslip_done(self):
        #res = super(HrPayslip, self).action_payslip_done()
        tipo_de_poliza = self.env['ir.config_parameter'].sudo().get_param('nomina_cfdi_conta_ee.tipo_de_poliza')
        if tipo_de_poliza=='Por nómina':
            payslips_with_batch = self.filtered(lambda x:x.payslip_run_id)
            payslips_without_batch = self - payslips_with_batch
            if payslips_without_batch:
                res = super(HrPayslipContaEE, payslips_without_batch).action_payslip_done()
                if not payslips_with_batch:
                    return res
            if payslips_with_batch:
                return super(HrPayslip, payslips_with_batch).action_payslip_done()
        else:
            return super(HrPayslipContaEE, self).action_payslip_done()
        
    
class HrPayslipRun(models.Model):
    _inherit = 'hr.payslip.run'
    
    #@api.depends('slip_ids', 'slip_ids.state')
    
#     @api.multi
    def _compute_is_all_payslip_done(self):
        tipo_de_poliza = self.env['ir.config_parameter'].sudo().get_param('nomina_cfdi_conta_ee.tipo_de_poliza')
        for batch in self:
            if tipo_de_poliza != 'Por nómina':
                batch.is_all_payslip_done = False
            else:    
                statuses = batch.slip_ids.mapped('state')
                if len(set(statuses))==1 and statuses[0]=='done':
                    batch.is_all_payslip_done = True
                else: 
                    batch.is_all_payslip_done = False
    
    is_all_payslip_done = fields.Boolean("Is all Payslip Done?", compute='_compute_is_all_payslip_done')
    move_id = fields.Many2one('account.move', 'Accounting Entry', readonly=True, copy=False)
    
#     @api.multi
    def action_crear_poliza(self):
        precision = self.env['decimal.precision'].precision_get('Payroll')
        payslip_obj = self.env['hr.payslip']
        for slip_batch in self:
            slips_confirm = slip_batch.slip_ids.filtered(lambda x:x.state in ['draft', 'waiting'])
            if slips_confirm:
                slips_confirm.action_payslip_done()
            line_ids = []
            debit_sum = 0.0
            credit_sum = 0.0
            date = slip_batch.date_end
            currency = slip_batch.journal_id.company_id.currency_id

            slip_batch_journal_id = slip_batch.journal_id.id
            name = _('Payslip batch of %s') % (slip_batch.name)
            move_dict = {
                'narration': name,
                'ref': slip_batch.name,
                'journal_id': slip_batch_journal_id,
                'date': date,
            }
            payslips = payslip_obj.browse()
            for slip in slip_batch.slip_ids:
                if slip.move_id:
                    continue
                for line in slip.details_by_salary_rule_category:
                    amount = currency.round(slip.credit_note and -line.total or line.total)
                    if currency.is_zero(amount): #float_is_zero(amount, precision_digits=precision):
                        continue

                    department_id = slip.employee_id.contract_id and slip.employee_id.contract_id.department_id and slip.employee_id.contract_id.department_id.id or False
                    #obtener la cuenta de debito
                    debit_analytic_account_id = slip.contract_id.analytic_account_id.id
                    debit_account_id = False
                    if department_id:
                        deudoras = line.salary_rule_id.cta_deudora_ids.filtered(lambda x:x.department_id.id==department_id and x.account_credit)
                        if deudoras:
                            debit_account_id = deudoras[0].account_credit.id
                            if deudoras[0].account_analytic and not debit_analytic_account_id:
                               debit_analytic_account_id = deudoras[0].account_analytic.id
                    if not debit_account_id:
                        debit_account_id = line.salary_rule_id.account_debit.id
                    if not debit_analytic_account_id:
                        debit_analytic_account_id = line.salary_rule_id.analytic_account_id.id

                    #obtener la cuenta de crédito
                    credit_analytic_account_id = slip.contract_id.analytic_account_id.id
                    credit_account_id = False
                    if department_id:
                        contabilidads = line.salary_rule_id.cta_acreedora_ids.filtered(lambda x:x.department_id.id==department_id and x.account_credit)
                        if contabilidads:
                            credit_account_id = contabilidads[0].account_credit.id
                            if contabilidads[0].account_analytic and not credit_analytic_account_id:
                               credit_analytic_account_id = contabilidads[0].account_analytic.id
                    if not credit_account_id:
                        credit_account_id = line.salary_rule_id.account_credit.id
                    if not credit_analytic_account_id:
                        credit_analytic_account_id = line.salary_rule_id.analytic_account_id.id

                    if debit_account_id:
                        debit_line = (0, 0, {
                            'name': line.name,
                            'partner_id': line._get_partner_id(credit_account=False),
                            'account_id': debit_account_id,
                            'journal_id': slip_batch_journal_id, #slip.journal_id.id,
                            'date': date,
                            'debit': amount > 0.0 and amount or 0.0,
                            'credit': amount < 0.0 and -amount or 0.0,
                            'analytic_account_id': debit_analytic_account_id,
                            'tax_line_id': line.salary_rule_id.account_tax_id.id,
                        })
                        line_ids.append(debit_line)
                        debit_sum += debit_line[2]['debit'] - debit_line[2]['credit']
    
                    if credit_account_id:
                        credit_line = (0, 0, {
                            'name': line.name,
                            'partner_id': line._get_partner_id(credit_account=True),
                            'account_id': credit_account_id,
                            'journal_id': slip_batch_journal_id, #slip.journal_id.id,
                            'date': date,
                            'debit': amount < 0.0 and -amount or 0.0,
                            'credit': amount > 0.0 and amount or 0.0,
                            'analytic_account_id': credit_analytic_account_id,
                            'tax_line_id': line.salary_rule_id.account_tax_id.id,
                        })
                        line_ids.append(credit_line)
                        credit_sum += credit_line[2]['credit'] - credit_line[2]['debit']
                payslips += slip

            if currency.compare_amounts(credit_sum, debit_sum) == -1:
                    acc_id = slip_batch.journal_id.default_account_id.id
                    if not acc_id:
                        raise UserError(_('El diario de gasto "%s" no tiene configurado la cuenta de crédito') % (slip_batch.journal_id.name))
                    adjust_credit = (0, 0, {
                        'name': _('Entrada de ajuste'),
                        'partner_id': False,
                        'account_id': acc_id,
                        'journal_id': slip_batch.journal_id.id,
                        'date': date,
                        'debit': 0.0,
                        'credit': currency.round(debit_sum - credit_sum),
                    })
                    line_ids.append(adjust_credit)
            elif currency.compare_amounts(debit_sum, credit_sum) == -1:
                    acc_id = slip_batch.journal_id.default_account_id.id
                    if not acc_id:
                        raise UserError(_('El diario de gasto "%s" no tiene configurado la cuenta de débito') % (slip_batch.journal_id.name))
                    adjust_debit = (0, 0, {
                        'name': _('Entrada de ajuste'),
                        'partner_id': False,
                        'account_id': acc_id,
                        'journal_id': slip_batch.journal_id.id,
                        'date': date,
                        'debit': currency.round(credit_sum - debit_sum),
                        'credit': 0.0,
                    })
                    line_ids.append(adjust_debit)
            
            res_config = self.env['res.config.settings'].search([], order='id desc', limit=1)
            compacta = res_config.compacta
            tipo_de_poliza = res_config.tipo_de_poliza
            new_dict = {}
            new_list = []
            items = []
            if tipo_de_poliza == 'Por nómina' and compacta == True:
                for line in line_ids:
                    account_id = line[2].get('account_id')
                    new_list = line[2]
                    for key, val in new_dict.items():
                        if key == account_id:
                            credit = line[2].get('credit') + val.get('credit')
                            debit = line[2].get('debit') + val.get('debit')
                            new_list['credit'] = credit
                            new_list['debit'] = debit
                    new_dict.update({account_id: new_list})
                
                for data,item in new_dict.items():
                    items.append((0, 0, item))
                line_ids = items
                    
            if line_ids:
                move_dict['line_ids'] = line_ids
                move = self.env['account.move'].create(move_dict)
                slip_batch.write({'move_id': move.id})
                payslips.write({'move_id': move.id, 'date': date})
                move.post()
        return True

class HrSalaryRule(models.Model):
    _inherit = 'hr.salary.rule'

    cta_deudora_ids = fields.One2many('nomina.deudora', 'doc_id', 'cta_deudora')
    cta_acreedora_ids = fields.One2many('nomina.acreedora', 'doc_id', 'cta_acreedora')

class ContabilidadNomina(models.Model):
    _name = "nomina.deudora"

    doc_id = fields.Many2one('hr.salary.rule', 'Cuentas contables')
    department_id = fields.Many2one('hr.department', string='Departmento')
    account_credit = fields.Many2one('account.account', 'Cuenta contable', domain=[('deprecated', '=', False)])
    account_analytic = fields.Many2one('account.analytic.account', 'Cuenta analítica')

class ContabilidadNomina(models.Model):
    _name = "nomina.acreedora"

    doc_id = fields.Many2one('hr.salary.rule', 'Cuentas contables')
    department_id = fields.Many2one('hr.department', string='Departmento')
    account_credit = fields.Many2one('account.account', 'Cuenta contable', domain=[('deprecated', '=', False)])
    account_analytic = fields.Many2one('account.analytic.account', 'Cuenta analítica')
