from odoo import api, fields, models, _, tools
from datetime import datetime, timedelta
from odoo.exceptions import UserError, RedirectWarning, ValidationError
from odoo.osv import osv, expression
import logging
_logger = logging.getLogger(__name__)
import re

_estructura_ubicacion = re.compile('(OR|DE)[0-9]{6}')
class SaleOrder(models.Model):
    _inherit = "sale.order"       
    
    
    carta_porte = fields.Selection([
        ('cartaporte', 'Carta Porte'),                   
        ], string='Complemento', copy=False, index=True)

    """def action_confirm(self):
        _logger.info('función activa heredada')
        #_logger.error('cantidad: %s', self.order_line.product_id.qty_available)
        
        if self._get_forbidden_state_confirm() & set(self.mapped('state')):
            raise UserError(_(
                'It is not allowed to confirm an order in the following states: %s'
            ) % (', '.join(self._get_forbidden_state_confirm())))

        for order in self.filtered(lambda order: order.partner_id not in order.message_partner_ids):
            order.message_subscribe([order.partner_id.id])
        self.write({
            'state': 'sale',
            'date_order': fields.Datetime.now()
        })

        # Context key 'default_name' is sometimes propagated up to here.
        # We don't need it and it creates issues in the creation of linked records.
        context = self._context.copy()
        context.pop('default_name', None)

        self.with_context(context)._action_confirm()
        if self.env.user.has_group('sale.group_auto_done_setting'):
            self.action_done()
        if self.carta_porte:
            for picking in self.picking_ids:
                picking.carta_porte = self.carta_porte
                picking.tipo_seguro_civil = True
                for mv in picking.move_ids_without_package:
                    _logger.info('asignación')
                    if mv.product_id.sat_product_id.MaterialPeligroso =='1':
                        picking.tipo_seguro_amb = True
                        vals = {
                                "stock_picking_id": picking.id,
                                "product_id": mv.product_id.id,
                                "product_qty": mv.product_uom_qty,
                                "materialpeligroso": 'si',
                                
                              }
                    else:
                        vals = {
                                "stock_picking_id": picking.id,
                                "product_id": mv.product_id.id,
                                "product_qty": mv.product_uom_qty,
                                "materialpeligroso": 'no'
                              }

                    self.env['mercancias'].create(vals)

                vals_contac = {
                            'picking_id': picking.id,
                            'TipoUbicacion': 'origen',                                                        
                            'partner_id_t': picking.company_id.id
                    }
                self.env['ubicaciones'].create(vals_contac)

                vals_contac_client = {
                            'picking_id': picking.id,
                            'TipoUbicacion': 'destino',                                                        
                            'partner_id_t': picking.partner_id.id
                    }
                self.env['ubicaciones'].create(vals_contac_client)


                    
                
                
            
        return True"""

class ubicaciones(models.Model):
    _name = 'ubicaciones'

    picking_id = fields.Many2one('stock.picking', string='picking')
    TipoUbicacion = fields.Selection([
        ('origen', 'Origen'),
        ('destino', 'Destino'),             
        ], string='Tipo de Ubicación', copy=False, index=True)
    IDUbicacion = fields.Char('ID de ubicación', compute='_compute_ubicación', readonly=True)
    partner_id_t = fields.Many2one('res.partner', string='Contacto')

    @api.model
    @api.depends('TipoUbicacion')
    def _compute_ubicación(self):
        for rec in self: 
            if rec.TipoUbicacion == 'origen':
                rec.IDUbicacion = self.env['ir.sequence'].next_by_code('origenes') or ('')
                rec.IDUbicacion = rec.IDUbicacion.replace('/', '')
            elif rec.TipoUbicacion == 'destino':
                rec.IDUbicacion = self.env['ir.sequence'].next_by_code('destinos') or ('')
                rec.IDUbicacion = rec.IDUbicacion.replace('/', '')
            else:
                rec.IDUbicacion = ""

     


    @api.constrains('IDUbicacion')
    def _check_idubicacion(self):
        for rec in self:
            if rec.IDUbicacion:
                if not _estructura_ubicacion.match(rec.IDUbicacion):
                    raise UserError(_('Error!\nLa estructura del ID de ubicación debe ser de la siguiente manera:\n para origen el acrónimo “OR” o para destino el acrónimo “DE” seguido de 6 dígitos numéricos asignados por el contribuyente que emite el comprobante para su identificación.\n Ej.origen OR101010, destino DE202020'))
    @api.constrains('picking_id')
    def _check_tipoubicacion(self):  
         
        ubicacion = len(self.search([('TipoUbicacion','=', 'origen'), ('picking_id','=',self.picking_id.id)]))
       
        if ubicacion and (ubicacion > 1):
            raise ValidationError("No puede haber mas de una ubicación de tipo Origen")  












       