# -*- encoding: utf-8 -*-
from odoo import api, fields, models, _


class account_journal(models.Model):
    _inherit = 'account.journal'

    
    use_for_cfdi = fields.Boolean(string="Permitir Timbrado")
    sat_tipo_poliza_id = fields.Many2one('account.journal.types', 'Tipo de póliza')
    cmlp_type_id = fields.Selection([('check', 'Cheque'), ('transfer', 'Transferencia'), ('other', 'Otro Método de pago')], string='Tipo de Complento')
    payment_method_id = fields.Many2one('eaccount.payment.methods','Método de pago SAT')
    account_credit_id = fields.Many2one('res.partner.bank', 'Cuenta bancaria acreedora')                                         
    account_debit_id = fields.Many2one('res.partner.bank', 'Cuenta bancaria deudora')
    address_invoice_company_id = fields.Many2one('res.partner', string='Dirección de Emisión', 
                                                 domain="[('type', 'in', ('invoice','default','contact'))]",
        help="Si este campo es capturado, la factura electrónica tomará los datos de la dirección del partner seleccionado para generar el CFDI")
    company2_id = fields.Many2one('res.company', string='Compañía Emisora',
        help="Si este campo es capturado, la factura electrónica tomará los datos de la Compañía seleccionada como Compañía emisora del CFDI")
    report_id_fact   = fields.Many2one('ir.actions.report', string='Reporte Facturas', 
                                 help="""Esta plantilla de reporte se usará para la generación de la representación del PDF del CFDI""")
    report_id_pay   = fields.Many2one('ir.actions.report', string='Reporte Recepcion de Pagos', 
                                 help="""Esta plantilla de reporte se usará para la generación de la representación del PDF del CFDI""")
    poliza_cierre = fields.Boolean(string="Póliza de Resultados")
    anticipo = fields.Boolean(string='Aplicar Anticipo', defaut=False)

    @api.model
    @api.constrains('poliza_cierre')    
    def _check_journal_closing_fy(self):
        if self.poliza_cierre and self.type != 'general':
            raise UserError(_('Advertencia !\nSolo puede marcar el Diario "Póliza de Resultados" si es de tipo "Misceláneo". Si tiene mas de uno marcado entonces se tomará el primero que haya sido registrado'))

    


class AccountMove(models.Model):
    _inherit = "account.move"
    
    poliza_cierre = fields.Boolean(string="Póliza de Resultados", default=False, readonly=True)