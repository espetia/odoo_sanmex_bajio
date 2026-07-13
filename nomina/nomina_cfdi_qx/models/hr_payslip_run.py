# -*- coding: utf-8 -*-

from odoo import api, models, fields
import logging
_logger = logging.getLogger(__name__)

class HrPayslipRun(models.Model):
    _inherit = 'hr.payslip.run'

    state = fields.Selection([
        ('draft', 'Draft'),
        ('done', 'Done'),
        ('close', 'Close'),
    ], string='Status', index=True, readonly=True, copy=False, default='draft')

    def confirmar_todas(self):
        for slip_id in self.slip_ids:
            if slip_id.state == 'draft':
                slip_id.action_payslip_done()
        self.state = 'done'

    def reversar_todas(self):
        for slip_id in self.slip_ids:
            if slip_id.state == 'done':
                slip_id.action_payslip_cancel()
                slip_id.action_payslip_draft()
        self.state = 'draft'

    def timbrar_nomina(self):
        self.ensure_one()
        #cr = self._cr
        payslip_obj = self.env['hr.payslip']
        for payslip_id in self.slip_ids.ids:
            payslip = payslip_obj.browse(payslip_id)

            # if payslip.state in ['draft','verify']:
            if payslip.state in ['verify','done'] and payslip.estado_factura == 'factura_no_generada':
               #_loggetttttttttttttttr.info('ejecuta nomina')
               payslip.action_payslip_done()
               if payslip.nomina_cfdi == False:
                   _logger.info('ejecuta nomina')
                   payslip.action_cfdi_nomina_generate()
               
        return