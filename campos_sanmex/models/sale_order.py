# -*- encoding: utf-8 -*-

from odoo import api, fields, models, _
from odoo.exceptions import UserError, RedirectWarning, ValidationError
import logging
_logger = logging.getLogger(__name__)


class SaleOrder(models.Model):
    _inherit = "sale.order"    

    calle_entrega = fields.Char('Calle Entrega', readonly=True)
    cantidad = fields.Char('CANTIDAD')
    cantidad_1 = fields.Char('Cantidad / Modelo / Color')
    cobrar_en_entrega = fields.Boolean('Cobrar en Entrega')
    color = fields.Char('Color:')
    color_1 = fields.Char('Color')
    contacto_que_recibe = fields.Char('Contacto que Recibe')
    direccin_actual = fields.Char('Dirección Actual')
    excelente = fields.Char('EXCELENTE')
    firma_del_cliente = fields.Char('FIRMA DEL CLIENTE')
    gerente_de_sucursal = fields.Char('Gerente de Sucursal')
    link_de_ubicacin = fields.Char('Link de Ubicación:')
    modelo = fields.Char('Modelo')
    n_cliente_contratista = fields.Char('N-Cliente Contratista:')
    no_cliente = fields.Char('No. Cliente', readonly=True)
    nombre_de_sucursal = fields.Char('Nombre de Sucursal')
    nombre_obra_o_proyecto = fields.Char('Nombre Obra o Proyecto')
    nombre_prospecto = fields.Char('Nombre Prospecto')
    numero_de_sucursal = fields.Char('Numero de Sucursal')
    operador = fields.Selection([('operador', 'Operador')], string="Operador", readonly=True)
    operador_unidad = fields.Char('Operador')
    pn_nombre_de_obraproyecto = fields.Char('PN-Nombre de Obra/Proyecto:', readonly=True)
    pr_cliente_contratista = fields.Char('PR Cliente Contratista:', readonly=True)
    puesto = fields.Char('Puesto')
    rea_de_entrega = fields.Text('Área de Entrega:')
    ref_entrega = fields.Char('Ref. Entrega:')
    related_field_fwB8p = fields.Char('PR Nombre de Obra:',)
    rv_nombre_obra = fields.Char('RV Nombre Obra:', readonly=True)
    tel_de_quien_recibe = fields.Char('Tel. de quien recibe')
    vista_de_direccin = fields.Char('Vista de Dirección:', readonly=True)
    vrd_entrega = fields.Char('VRD Entrega:')
    fecha_entrega_log = fields.Date('Fecha de entrega', help="Fecha de entrega logistica")
    contacto_de_solicitud = fields.Char('Contacto de Solicitud')
    telefono_solicitud = fields.Char('Teléfono')
    correo_solicitud = fields.Char('Correo')
    referencia_entrega = fields.Char('Ref. Entrega')
    fecha_retiro = fields.Date('Fecha de retiro')
    description_rb = fields.Char('Descripcion')
    cantidad_rb = fields.Char('Cantidad')

class AccountMove(models.Model):  
    _inherit ='account.move'

    fecha_de_cancelacin = fields.Date('Fecha de Cancelación')
    fecha_de_pago = fields.Char(string='Fecha de pago', compute="_compute_fecha_pago")

    @api.depends('payment_state')
    def _compute_fecha_pago(self):
        for move in self:
            if move.payment_state not in ['paid', 'in_payment']:
                move.fecha_de_pago = ''
            else:
                payments = move._get_reconciled_payments()
                _logger.info("Payment"+str(payments))
                if payments:
                    move.fecha_de_pago = ','.join([pay.date.strftime("%d/%m/%Y") for pay in payments if pay.invoice_line_ids])
                    _logger.info("Payment"+str(move))
                else:
                    move.fecha_de_pago = ''