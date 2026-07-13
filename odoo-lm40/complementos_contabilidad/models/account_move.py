# -*- encoding: utf-8 -*-

from odoo import api, fields, models, _
from odoo.exceptions import UserError, ValidationError
import re

_RFC_PATTERN = re.compile('[A-Z\xc3\x91&]{3,4}[0-9]{2}[0-1][0-9][0-3][0-9][A-Z0-9]?[A-Z0-9]?[0-9A-Z]?')
_SERIES_PATTERN = re.compile('[A-Z]+')
_UUID_PATTERN = re.compile('[a-f0-9A-F]{8}-[a-f0-9A-F]{4}-[a-f0-9A-F]{4}-[a-f0-9A-F]{4}-[a-f0-9A-F]{12}')

class account_move_fit(models.Model):
    _inherit = 'account.move'
    

    item_concept        = fields.Char(string='Concepto', size=300)
    complement_line_ids = fields.One2many('eaccount.complements', 'move_id', string="Complementos")

    _PERIOD_NAMES = {
                    '01': 'ENERO',
                    '02': 'FEBRERO',
                    '03': 'MARZO',
                    '04': 'ABRIL',
                    '05': 'MAYO',
                    '06': 'JUNIO',
                    '07': 'JULIO',
                    '08': 'AGOSTO',
                    '09': 'SEPTIEMBRE',
                    '10': 'OCTUBRE',
                    '11': 'NOVIEMBRE',
                    '12': 'DICIEMBRE'
                    }

    @api.model
    def launch_period_validator(self):
        if not len(self._context['active_ids']):
            raise UserError(_('Ningún registro seleccionado\n\nDebe seleccionar al menos una póliza para procesar.'))
        all_periods = set([ x.period_id for x in self ])
        if len(all_periods) > 1:
            raise UserError(_('Advertencia !!!\n\nSe ha encontrado más de un periodo fiscal\nTodas las pólizas seleccionadas deben pertenecer al mismo periodo fiscal.'))
        period_id = all_periods.pop()
        ctx = self._context.copy()
        ctx['period_id'] = period_id.id
        return {
                'type'      : 'ir.actions.act_window',
                'res_model' : 'vouchers.xml.creator',
                'view_mode' : 'form',
                'view_type' : 'form',
                'name'      : 'Parámetros del XML',
                'target'    : 'new',
                'context'   : ctx,
                }



    #@api.model
    def action_post(self):
        for move in self:
            for ln in move.line_ids:
                
                for cmpl in ln.complement_line_ids + move.complement_line_ids:
                    location = ' en Auxiliar de folios' if cmpl.move_id else ' en complementos por asiento'
                    if cmpl.origin_bank_id and not cmpl.origin_bank_id.sat_bank_id:
                        raise UserError(_('Datos faltantes %s.\nEl banco "%s" no tiene asignado un código del SAT') % (location, cmpl.origin_bank_id.name))
                    if cmpl.origin_bank_id and cmpl.origin_bank_id.sat_bank_id.bic == '999' and not cmpl.origin_frgn_bank:
                        raise UserError(_('Datos faltantes %s.\nEl banco "%s" está marcado como extranjero, pero una línea de su complemento no contiene el nombre del banco.') % (location, cmpl.origin_bank_id.name))
                    if cmpl.destiny_bank_id and not cmpl.destiny_bank_id.sat_bank_id:
                        raise UserError(_('Datos faltantes %s.\nEl banco "%s" no tiene asignado un código del SAT') % (location, cmpl.destiny_bank_id.name))
                    if cmpl.destiny_bank_id and cmpl.destiny_bank_id.sat_bank_id.bic == '999' and not cmpl.destiny_frgn_bank:
                        raise UserError(_('Datos faltantes %s.\nEl banco "%s" está marcado como extranjero, pero una línea de su complemento no contiene el nombre del banco.') % (location, cmpl.destiny_bank_id.name))
                    if cmpl.uuid and len(cmpl.uuid) != 36 or cmpl.uuid and not _UUID_PATTERN.match(cmpl.uuid.upper()):
                        raise UserError(_('Información incorrecta %s.\nEl UUID "%s" no se apega a los lineamientos del SAT.') % (location, cmpl.uuid))
                    if cmpl.rfc and not _RFC_PATTERN.match(cmpl.rfc):
                        raise UserError(_('Información incorrecta %s.\nEl RFC "%s" no es válido con respecto a los lineamientos del SAT.') % (location, cmpl.rfc))
                    if cmpl.rfc2 and not _RFC_PATTERN.match(cmpl.rfc2):
                        raise UserError(_('Información incorrecta %s.\nEl RFC "%s" no es válido con respecto a los lineamientos del SAT.') % (location, cmpl.rfc2))
                    


        return super(account_move_fit, self).action_post()


    #@api.model
    def edit_complements(self):
        self.ensure_one()
        view_id = self.env['ir.ui.view'].search([('name', 'ilike', 'move.complements.form')])
        return {'type'      : 'ir.actions.act_window',
                'res_id'    : self.id,
                'res_model' : 'account.move',
                'view_mode' : 'form',
                'view_type' : 'form',
                'target'    : 'new',
                'view_id'   : view_id.id,
                'name'      : _('Contabilidad electrónica - Auxiliares de folios'),
               }


    @api.model
    def save_complements(self):
        return True



class vouchers_xml_holder(models.TransientModel):
    _name = 'vouchers.xml.creator'
    

    vouchers_reqtype = fields.Selection([('AF', 'Acto de fiscalización'),
                                         ('FC', 'Fiscalización compulsa'),
                                         ('DE', 'Devolución'),
                                         ('CO', 'Compensación')], 
                                        string='Tipo de solicitud', required=True, default=lambda *a: 'DE')
    vouchers_ordnum  = fields.Char(string='Número de orden', size=13)
    vouchers_procnum = fields.Char(string='Número de trámite', size=10)
    

    @api.model
    def start_processing(self):
        period = self.env['account.period'].browse(self._context['period_id'])
        wizVals = {'xml_target'   : self._context.get('target', 'vouchers'),
                   'month'        : period.date_start[5:7],
                   'year'         : int(period.date_start[0:4]),
                   'request_type' : self.vouchers_reqtype,
                   'order_number' : self.vouchers_ordnum,
                   'procedure_number': self.vouchers_procnum,
                  }
        wizId = self.env['files.generator.wizard'].create(wizVals)
        return wizId.process_file(moveIds=self._context['active_ids'])




