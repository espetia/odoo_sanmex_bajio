from odoo import api, fields, models, _, tools
import time
import dateutil
import dateutil.parser
from datetime import datetime, date, timedelta
import requests
import json
import urllib
import traceback
import qrcode
import codecs
import os
import sys
import io
import time as ti
from pytz import timezone
import pytz
import base64
from odoo.tools import DEFAULT_SERVER_DATETIME_FORMAT, DEFAULT_SERVER_DATE_FORMAT
from odoo.exceptions import UserError, RedirectWarning, ValidationError
from odoo.osv import osv, expression
import logging
_logger = logging.getLogger(__name__)
import re


_estructura_placa = re.compile('^(?!.*\s)-]{5,7}')
_estructura_año = re.compile('19[0-9]{2}|20[0-9]{2}')
_estructura_dimenciones = re.compile('([0-9]{1,3}[/]){2}([0-9]{1,3})(cm|plg)')
class stock_picking(models.Model):
    _inherit = "stock.picking"

    @api.depends('mercancias_ids.peso')
    def total_peso(self):
        """
        Compute the total amounts of the SO.
        """
        for rec in self:
            peso_total = 0.0
            
            for lines in rec.mercancias_ids:
                
                peso_total += lines.peso
                
            rec.update({
                'PesoBrutoTota': peso_total,
                
            })


    

    figuratrasnporte_ids = fields.One2many('figuratransporte', 'picking_id', string="Figura Transporte", copy=False)
    carta_porte = fields.Selection([
        ('cartaporte', 'Carta Porte'),                   
        ], string='Complemento', copy=False, index=True)
    is_federal = fields.Boolean('Carretera Federal')
    trasporte_vehiculo = fields.Many2one('fleet.vehicle', string='Vehículo para Transporte', domain="[('vehiculo_is', '=', True),('categoiria_vehiculo', '=', 'vehiculo')]")
    ubicaciones_ids = fields.One2many('ubicaciones', 'picking_id', string="Ubicaciones", copy=False)
    tipo_seguro_civil = fields.Boolean('Reponsabilidad Civil')
    tipo_seguro_amb = fields.Boolean('Medio Ambiente')
    tipo_seguro_carga = fields.Boolean('Carga')
    tipo_seguro_vmercancia = fields.Boolean('Prima Seguro')                                    
    asegurado_civil = fields.Many2one('cat.seguros', string='Aseguradora/Póliza', domain="[('tipo_seguro', '=', 'AseguraRespCivil'),('state','=', 'vigente')]")
    asegurado_amb = fields.Many2one('cat.seguros', string='Aseguradora/Póliza', domain="[('tipo_seguro', '=', 'AseguraMedAmbiente'),('state','=', 'vigente')]")
    asegurado_carga = fields.Many2one('cat.seguros', string='Aseguradora/Póliza', domain="[('tipo_seguro', '=', 'AseguraCarga'),('state','=', 'vigente')]")
    asegurado_vmercancia = fields.Float(string='Prima de Seguro')
    CargoPorTasacion = fields.Float('Cargo por Tasación')
    fechaHorasalidallegada_origen = fields.Datetime('Fecha/Hora Salida')
    fechaHorasalidallegada_destino = fields.Datetime('Fecha/Hora LLegada')
    distanciarecorrida = fields.Char('Distancia Recorrida')
    PesoBrutoTota = fields.Char(compute='total_peso', string='Peso Bruto Total')
    UnidadPeso = fields.Many2one('c_claveunidadpeso', string='Unidad de Peso')    
    remolques_ids = fields.One2many('remolque_picking', 'picking_id', string="Remolques")
    TranspInternac = fields.Selection([
        ('si', 'Sí'),
        ('no', 'No'),             
        ], string='Transporte Internacional', copy=False, index=True, default='no') 

    EntradaSalidaMerc = fields.Selection([
        ('in', 'Entrada'),
        ('out', 'Salida'),             
        ], string='Entrada o Salida de mercancías ', copy=False, index=True, default=False)

    PaisOrigenDestino = fields.Many2one('res.country.sat.code', string='País Origen/Destino')
    ViaEntradaSalida = fields.Many2one('c_cvetransporte', string='Via de Salida/Entrada')
    mercancias_ids = fields.One2many('mercancias', 'stock_picking_id', string='Mercancías')

    #######Campos para guardar información de CFDI########
    state_sat = fields.Selection([('validate', 'Timbrada'), ('no_cfdi', ' No Timbrada')], string="Estatus Sat", readonly=True, default='no_cfdi', copy=False)
    pac_timbre = fields.Char('Pac', readonly=True, copy=False)
    Sello = fields.Text('Sello',  readonly=True, help='Sign assigned by the SAT', copy=False)
    NoCertificado = fields.Char('No. Certificado Emisor', size=32, readonly=True,
                                       help='Serial Number of the Certificate', copy=False)
    cfdi_cadena_original = fields.Text(string='Cadena Original', readonly=True,
                                        help='Original String used in the electronic invoice', copy=False)
    FechaTimbrado = fields.Datetime(string='Fecha Timbrado', readonly=True,
                                           help='Date when is stamped the electronic invoice', copy=False)
    cfdi_fecha_cancelacion = fields.Datetime(string='Fecha Cancelación', readonly=True,
                                             help='Fecha cuando la factura es Cancelada', copy=False)
    UUID = fields.Char(string='Folio Fiscal (UUID)', size=64, readonly=True,
                                     help='Folio Fiscal del Comprobante CFDI, también llamado UUID', copy=False)
    cfdi_cbb = fields.Binary('Imagen Código Bidimencional', copy=False)
    sello = fields.Text('Sello', size=512, help='Digital Stamp', copy=False)
    certificado = fields.Text('Certificado', size=64, help='Certificate used in the invoice', copy=False)
    cadena_original = fields.Text('String Original', help='Data stream with the information contained in the electronic invoice')
    no_certificado  = fields.Char(string='No. Certificado Sat', size=64, help='Number of serie of certificate used for the invoice', copy=False)
    name_invoice = fields.Char(compute='_get_invoice_traslado', string='Factura')
    TipoDeComprobante = fields.Many2one('sat.tipo.comprobante', 'Tipo de Comprobante', required=False, copy=False)
    partner_owner = fields.Many2one(related="trasporte_vehiculo.partner_owner", string="Propietario", domain="[('is_owner', '=', True)]")

    @api.onchange('trasporte_vehiculo')
    def _compute_remolques(self):
        if self.trasporte_vehiculo:
            #_logger.info('vehiculo') 
            for remolque in self.trasporte_vehiculo.remolques_ids:
                auto = self.env['fleet.vehicle'].search([('id','=', remolque.id)])
                autos = []
                vals = {
                        'picking_id': self.id,
                       'remolque_id': auto.id 

                }
                remo = self.env['remolque_picking'].create(vals)
                _logger.error('datos: %s', remo.SubTipoRem.Clave)

    def _get_invoice_traslado(self):
        

        fname = ""
        if not self.company_id.partner_id.rfc and not self.company_id.partner_id.rfc :
            raise UserError(_("Error!\nLa Compañía Emisora no tiene definido el RFC."))
        fname += (self.company_id.partner_id.rfc or self.company_id.partner_id.rfc) + '_' + (self.name or '')
        
        self.name_invoice = fname

    @api.model
    def create(self, vals_list):
        res = super(stock_picking, self).create(vals_list)
        sat_tipo_obj = self.env['sat.tipo.comprobante']   
        
        tipo_id = sat_tipo_obj.search([('code','=','T')], limit=1)
        res.TipoDeComprobante = tipo_id[0].id if tipo_id else False
        


        return res

    @api.model
    def do_something_with_xml_attachment(self, attach):

        return True

    def timbra_traslado(self):
        login = {}
        webservice_url = self.env['ir.config_parameter'].sudo().get_param('webservice.url')
        multi_company = self.env['ir.config_parameter'].sudo().get_param('webservice.multi_company')
       
        
        if multi_company == False:
           
            login = {
            "rfc": self.env['ir.config_parameter'].sudo().get_param('webservice.rfc_web'),
            "clave": self.env['ir.config_parameter'].sudo().get_param('webservice.password')
            }
        else:
            _logger.info('condición aceptada')
            login = {
            "rfc": self.company_id.rfc_web_1,
            "clave": self.company_id.password_1
            }
        if webservice_url == 'test':
            url = self.env['ir.config_parameter'].sudo().get_param('webservice.url_name_prue')
        if webservice_url == 'product':
            url = self.env['ir.config_parameter'].sudo().get_param('webservice.url_name_produc')
        
        fname_invoice = self.name_invoice and self.name_invoice + \
                            '.xml' or ''
        nombreseguro = self.asegurado_civil.name
        nombreseguro = str(nombreseguro).encode("utf-8")
        base64_rfc = base64.b64encode(nombreseguro)
        nombreseguro_civil = base64_rfc.decode("utf-8")

        nombreseguro_carga = ''
        nombreseguro_amb = ''
        if self.tipo_seguro_amb:
            nombreseguro = self.asegurado_amb.name
            nombreseguro = str(nombreseguro).encode("utf-8")
            base64_rfc = base64.b64encode(nombreseguro)
            nombreseguro_amb = base64_rfc.decode("utf-8")
        if self.tipo_seguro_carga:
            nombreseguro = self.asegurado_carga.name
            nombreseguro = str(nombreseguro).encode("utf-8")
            base64_rfc = base64.b64encode(nombreseguro)
            nombreseguro_carga = base64_rfc.decode("utf-8")

        rfc_emisor = self.company_id.rfc
        rfc_clie = str(rfc_emisor).encode("utf-8")
        base64_rfc = base64.b64encode(rfc_clie)
        rfc_dec = base64_rfc.decode("utf-8")

        rfc_receptor = self.partner_id.rfc.upper()
        rfc_prove = str(rfc_receptor).encode("utf-8")
        base64_rfc_prov = base64.b64encode(rfc_prove)
        rfc_dec_prov = base64_rfc_prov.decode("utf-8")

        name_emisor = self.company_id.name
        name_emi = str(name_emisor).encode("utf-8")
        base64_name_clie = base64.b64encode(name_emi)
        name_emi_dec = base64_name_clie.decode("utf-8")

        name_receptor = self.partner_id.name
        name_rec = str(name_receptor).encode("utf-8")
        base64_name_recp = base64.b64encode(name_rec)
        name_rec_dec = base64_name_recp.decode("utf-8")

        
        TiposFigura =[]
        ubicaciones= []        
        ubicacion = {}
        remolque = []
        Mercancia = []
        concepto = []
        for ubica in self.ubicaciones_ids:
            if self.picking_type_code == 'outgoing' or self.picking_type_code == 'internal':
                _logger.info('ventas')
                if ubica.TipoUbicacion == 'origen':
                    ubicaciones.append({
                                    "DistanciaRecorrida": '',
                                    "Domicilio": {
                                        "Calle": self.company_id.street or "",
                                        "CodigoPostal": self.company_id.codigopostal_sat_id.code,
                                        "Colonia":self.company_id.colonia_sat_id.code or "",
                                        "Estado": self.company_id.state_id.code,
                                        "Localidad": self.company_id.sat_localidad_id.code or "",
                                        "Municipio": self.company_id.sat_municipio_id.code or "",
                                        "NumeroExterior": self.company_id.num_external or "",
                                        "Pais": self.company_id.country_id.sat_code.code,
                                        "Referencia": self.company_id.partner_id.street2 or ''
                                    },
                                    "FechaHoraSalidaLlegada": self.fechaHorasalidallegada_origen and time.strftime('%Y-%m-%dT%H:%M:%S', time.strptime(str(self.fechaHorasalidallegada_origen), '%Y-%m-%d %H:%M:%S')),
                                    "IDUbicacion": ubica.IDUbicacion,
                                    "NombreRemitenteDestinatario": name_emi_dec,
                                    "RFCRemitenteDestinatario": rfc_dec,
                                    "TipoUbicacion":dict(ubica._fields['TipoUbicacion'].selection).get(ubica.TipoUbicacion)
                                }
                                )
                else:
                    ubicaciones.append({

                                "DistanciaRecorrida": self.distanciarecorrida,
                                "Domicilio": {
                                    "Calle": self.partner_id.street or "",
                                    "CodigoPostal": self.partner_id.sat_codigopostal_id.code,
                                    "Colonia": self.partner_id.colonia_sat_id.code or "",
                                    "Estado": self.partner_id.state_id.code,
                                    "Localidad": self.partner_id.sat_localidad_id.code or "",
                                    "Municipio": self.partner_id.sat_municipio_id.code or "",
                                    "NumeroExterior":self.partner_id.num_external or "",
                                    "Pais": self.partner_id.country_id.sat_code.code,
                                    "Referencia": self.partner_id.street2 or ''
                                },
                                "FechaHoraSalidaLlegada": self.fechaHorasalidallegada_destino and time.strftime('%Y-%m-%dT%H:%M:%S', time.strptime(str(self.fechaHorasalidallegada_destino), '%Y-%m-%d %H:%M:%S')),
                                "IDUbicacion": ubica.IDUbicacion,
                                "NombreRemitenteDestinatario": name_rec_dec,
                                "RFCRemitenteDestinatario": rfc_dec_prov,                                
                                "TipoUbicacion": dict(ubica._fields['TipoUbicacion'].selection).get(ubica.TipoUbicacion)
                            }
                    )
            else:
                _logger.info('compras')
                if ubica.TipoUbicacion == 'origen':
                    ubicaciones.append({
                                    "DistanciaRecorrida": '',
                                    "Domicilio": {
                                    "Calle": self.partner_id.street or "",
                                    "CodigoPostal": self.partner_id.sat_codigopostal_id.code,
                                    "Colonia": self.partner_id.colonia_sat_id.code or "",
                                    "Estado": self.partner_id.state_id.code,
                                    "Localidad": self.partner_id.sat_localidad_id.code or "",
                                    "Municipio": self.partner_id.sat_municipio_id.code or "",
                                    "NumeroExterior":self.partner_id.num_external or "",
                                    "Pais": self.partner_id.country_id.sat_code.code,
                                    "Referencia": self.partner_id.street2 or ''
                                },
                                "FechaHoraSalidaLlegada": self.fechaHorasalidallegada_destino and time.strftime('%Y-%m-%dT%H:%M:%S', time.strptime(str(self.fechaHorasalidallegada_destino), '%Y-%m-%d %H:%M:%S')),
                                "IDUbicacion": ubica.IDUbicacion,
                                "NombreRemitenteDestinatario": name_rec_dec,
                                "RFCRemitenteDestinatario": rfc_dec_prov,                                
                                "TipoUbicacion": dict(ubica._fields['TipoUbicacion'].selection).get(ubica.TipoUbicacion)
                                }
                                )
                else:
                    ubicaciones.append({

                                "DistanciaRecorrida": self.distanciarecorrida,
                                "Domicilio": {
                                        "Calle": self.company_id.street or "",
                                        "CodigoPostal": self.company_id.codigopostal_sat_id.code,
                                        "Colonia":self.company_id.colonia_sat_id.code or "",
                                        "Estado": self.company_id.state_id.code,
                                        "Localidad": self.company_id.sat_localidad_id.code or "",
                                        "Municipio": self.company_id.sat_municipio_id.code or "",
                                        "NumeroExterior": self.company_id.num_external or "",
                                        "Pais": self.company_id.country_id.sat_code.code,
                                        "Referencia": self.company_id.partner_id.street2 or ''
                                    },
                                    "FechaHoraSalidaLlegada": self.fechaHorasalidallegada_origen and time.strftime('%Y-%m-%dT%H:%M:%S', time.strptime(str(self.fechaHorasalidallegada_origen), '%Y-%m-%d %H:%M:%S')),
                                    "IDUbicacion": ubica.IDUbicacion,
                                    "NombreRemitenteDestinatario": name_emi_dec,
                                    "RFCRemitenteDestinatario": rfc_dec,
                                    "TipoUbicacion":dict(ubica._fields['TipoUbicacion'].selection).get(ubica.TipoUbicacion)
                            }
                    )

        ubicacion['Ubicacion'] = ubicaciones

        for fig in self.figuratrasnporte_ids:
            nombrefigura = fig.figuratrasnporte.name
            nombrefigura = str(nombrefigura).encode("utf-8")
            base64_nombre = base64.b64encode(nombrefigura)
            nombrefigura_dec = base64_nombre.decode("utf-8")

            rfcfigura = fig.rfcfigura
            rfcfigura = str(rfcfigura).encode("utf-8")
            base64_rfc = base64.b64encode(rfcfigura)
            rfcfigura_dec = base64_rfc.decode("utf-8")

            


            TiposFigura.append(

                            {
                               "NombreFigura": nombrefigura_dec,
                               "NumLicencia": fig.numlicencia,
                               "RFCFigura": rfcfigura_dec,                              
                               "TipoFigura": fig.tipofigura.Clave,
                               "PartesTransporte":[]

                                        }
                )
        if self.partner_owner:


            propietario = self.partner_owner.name
            nombrepropietario = str(propietario).encode("utf-8")
            base64_nombre_pro = base64.b64encode(nombrepropietario)
            nombrefigura_dec_prop = base64_nombre_pro.decode("utf-8")

            rfcpropietario = self.partner_owner.rfc
            rfcfigura_propi = str(rfcpropietario).encode("utf-8")
            base64_rfc_pro = base64.b64encode(rfcfigura_propi)
            rfcfigura_dec_prop = base64_rfc_pro.decode("utf-8")
            TiposFigura.append(

                        {
                           "NombreFigura": nombrefigura_dec_prop,                           
                           "RFCFigura": rfcfigura_dec_prop,                              
                           "TipoFigura": self.partner_owner.tipofigura.Clave,
                           "PartesTransporte":[{
                                             "ParteTransporte": self.trasporte_vehiculo.parte_transporte.Clave
                           }]

                                    }
                )


        for remol in self.remolques_ids:
            remolque.append(
                           {
                            "Placa": remol.license_plate,
                            "SubTipoRem": remol.SubTipoRem.Clave
                    }

                )
        i = 0
        for line in self.mercancias_ids:
            if line.para_cartaporte == True:
                nombreproducto = line.product_id.name
                nombreproducto = str(nombreproducto).encode("utf-8")
                base64_nombre = base64.b64encode(nombreproducto)
                nombreproducto_dec = base64_nombre.decode("utf-8")
                if line.product_id.sat_product_id.MaterialPeligroso == '1' or line.product_id.sat_product_id.MaterialPeligroso == '0,1':
                    if  line.materialpeligroso == 'si':
                        Mercancia.append({
                                        "BienesTransp": line.product_id.sat_product_id.code,
                                        "Cantidad": line.product_qty,
                                        "ClaveUnidad": line.product_uom.sat_uom_id.code,
                                        "Descripcion": nombreproducto_dec,
                                        "Dimensiones": line.dimensiones or '',
                                        "MaterialPeligroso": dict(line._fields['materialpeligroso'].selection).get(line.materialpeligroso),
                                        "Moneda": line.currency.name,
                                        "PesoEnKg": line.peso,
                                        "ValorMercancia":line.valorproducto or '',
                                        "Unidad": line.product_uom.name,
                                        "CveMaterialPeligroso": line.CveMaterialPeligroso.Clave,
                                        "Embalaje": merc.embalaje.CalveDesignacion,
                                        "DescripEmbalaje": merc.embalaje.Descripcion
                                            }
                            )
                        i +=1
                    else:
                        Mercancia.append({
                                        "BienesTransp": line.product_id.sat_product_id.code,
                                        "Cantidad": line.product_qty,
                                        "ClaveUnidad": line.product_uom.sat_uom_id.code,
                                        "Descripcion": nombreproducto_dec,
                                        "Dimensiones": line.dimensiones or '',
                                        "MaterialPeligroso": dict(line._fields['materialpeligroso'].selection).get(line.materialpeligroso),
                                        "Moneda": line.currency.name,
                                        "PesoEnKg": line.peso,
                                        "ValorMercancia":line.valorproducto or '',
                                        "Unidad": line.product_uom.name,
                                        "CveMaterialPeligroso": "",
                                        "Embalaje": '',
                                        "DescripEmbalaje": ''
                                            }
                            )
                        i +=1
                else:
                    Mercancia.append({
                                        "BienesTransp": line.product_id.sat_product_id.code,
                                        "Cantidad": line.product_qty,
                                        "ClaveUnidad": line.product_uom.sat_uom_id.code,
                                        "Descripcion": nombreproducto_dec,
                                        "Dimensiones": line.dimensiones or '',
                                        #"MaterialPeligroso": dict(line._fields['materialpeligroso'].selection).get(line.materialpeligroso),
                                        "Moneda": line.currency.name,
                                        "PesoEnKg": line.peso,
                                        "ValorMercancia":line.valorproducto or '',
                                        "Unidad": line.product_uom.name,
                                        "CveMaterialPeligroso": "",
                                        "Embalaje": '',
                                        "DescripEmbalaje": ''
                                            }
                            )
                    i +=1

        for line in self.mercancias_ids:
            if line.para_cartaporte == True:
                nombreproducto = line.product_id.name
                nombreproducto = str(nombreproducto).encode("utf-8")
                base64_nombre = base64.b64encode(nombreproducto)
                nombreproducto_dec = base64_nombre.decode("utf-8")
                if self.is_federal == True:
                    concepto.append({
                                    "Cantidad": 1.0,
                                    "ClaveProdServ": line.product_id.sat_product_id.code,
                                    "ClaveUnidad": line.product_uom.sat_uom_id.code,                         
                                    "Descripcion": nombreproducto_dec,                            
                                    "Importe": 1.0,                            
                                    "Unidad": line.product_uom.name,
                                    "ValorUnitario": 1.0,
                                    "NoIdentificacion" : "01",
                                    "ObjetoImp": "01"
                                }
                        )
                else:
                     concepto.append({
                                    "Cantidad": line.product_qty,
                                    "ClaveProdServ": line.product_id.sat_product_id.code,
                                    "ClaveUnidad": line.product_uom.sat_uom_id.code,                         
                                    "Descripcion": nombreproducto_dec,                            
                                    "Importe": 0.0,                            
                                    "Unidad": line.product_uom.name,
                                    "ValorUnitario": 0.0,
                                    "NoIdentificacion" : "01",
                                    "ObjetoImp": "01"
                                }
                        )
        tz = self.with_context(tz=self.env.user.partner_id.tz)
        fecha = self.date_done  
        fecha = fields.Datetime.context_timestamp(tz, fields.Datetime.from_string(fecha))        
        fecha = ti.strftime('%Y-%m-%dT%H:%M:%S', ti.strptime(str(fecha)[0:19], '%Y-%m-%d %H:%M:%S'))
        if self.is_federal == True:
            cata_porte = {
                        "localizacion-mx": {
                            "Documento": {
                                "Comprobante": {
                                    "Adenda": "",
                                    "Certificado": "", 
                                    
                                    "CfdiRelacionados": {},  
                                     "Complemento": {
                                   "TimbreFiscaldigital":{
                                          "TimbreFiscaldigital": "",
                                          "FechaTimbrado": "",
                                          "NoCertificadoSAT": "",
                                          "RfcProvCertif": "",
                                          "SelloCFD": "",
                                          "SelloSAT": "",
                                          "UUID": "",
                                          "Version": ""
                                            },
                                    "Pagos": {
                                            "Version": "",
                                            "Pago": [
                                            ]
                                          }
                                  },             
                                    "Complementos": [
                                    {
                                    "CartaPorte": 
                                    {
                                    "EntradaSalidaMerc": dict(self._fields['EntradaSalidaMerc'].selection).get(self.EntradaSalidaMerc) or '',
                                    "FiguraTransporte": {
                                        "TiposFigura": TiposFigura
                            },
                            "Mercancias": {
                                "Autotransporte": {
                                    "IdentificacionVehicular": {
                                        "AnioModeloVM": self.trasporte_vehiculo.model_year,
                                        "ConfigVehicular": self.trasporte_vehiculo.ConfigVehicular.Clave,
                                        "PlacaVM": self.trasporte_vehiculo.license_plate
                                    },
                                    "NumPermisoSCT": self.trasporte_vehiculo.NumPermisoSCT,
                                    "PermSCT":self.trasporte_vehiculo.PermSCT.Clave,
                                    "Remolques": {
                                        "Remolque": remolque
                                    },
                                    "Seguros": {
                                        "AseguraCarga": nombreseguro_carga or '',
                                        "AseguraMedAmbiente": nombreseguro_amb or '',
                                        "AseguraRespCivil": nombreseguro_civil,
                                        "PolizaCarga": self.asegurado_carga.polizacarga or '',
                                        "PolizaMedAmbiente": self.asegurado_amb.polizamedioambiente or '',
                                        "PolizaRespCivil": self.asegurado_civil.polizarespcivil,
                                        "PrimaSeguro": self.asegurado_vmercancia or ''
                                    }
                                },
                                "CargoPorTasacion": self.CargoPorTasacion or '',
                                "Mercancia": Mercancia,
                                "NumTotalMercancias": i,
                                "PesoBrutoTotal": self.PesoBrutoTota,
                                "UnidadPeso": self.UnidadPeso.Clave
                            },
                            "PaisOrigenDestino": self.PaisOrigenDestino.code or '',
                            "TotalDistRec": self.distanciarecorrida or '', 
                            "TranspInternac": dict(self._fields['TranspInternac'].selection).get(self.TranspInternac),
                            "Ubicaciones": ubicacion,
                            "Version": "2.0",
                            "ViaEntradaSalida": self.ViaEntradaSalida.ClaveTransporte or ''
                        }}],
                                        
                                    
                                    "Conceptos": {
                                        "Concepto": concepto
                                    },                                                
                                    "Emisor": {
                                        "Nombre": name_emi_dec,
                                        "RegimenFiscal": self.company_id.partner_id.regimen_fiscal_id.code,
                                        "Rfc": rfc_dec
                                    },
                                    "Fecha": fecha,
                                    "Folio": self.name,                           
                                    "LugarExpedicion": self.company_id.codigopostal_sat_id.code,
                                    "Exportacion": "01",
                                    "Moneda": "XXX",
                                    "NoCertificado": "",
                                    "Receptor": {
                                        "Nombre": name_emi_dec,
                                        "NumRegIdTrib": "",
                                        "RFc": rfc_dec,
                                        "ResidenciaFiscal": "",
                                        "UsoCFDI": 'S01',
                                        "RegimenFiscalReceptor": self.partner_id.regimen_fiscal_id.code,                    
                                        "DomicilioFiscalReceptor": self.company_id.codigopostal_sat_id.code
                                    },
                                    "Sello": "",
                                    "Serie": self.name,
                                    "Subtotal": "0",                
                                    "TipoDeComprobante": "T",
                                    "Total": "0",
                                    "Version": "3.3"
                                },
                                "Operacion": "TIMBRAR",
                                "TipoDocumento": "FACTURA"
                            },
                            "login": login
                        }

                        }
        else:
            cata_porte = {
                        "localizacion-mx": {
                            "Documento": {
                                "Comprobante": {
                                    "Adenda": "",
                                    "Certificado": "",   
                                     "CfdiRelacionados": {
                                        "CfdiRelacionado": "",                                                   
                                                                                        
                                        "TipoRelacion": "",
                                     },             
                                   "Complemento": {
                                   "TimbreFiscaldigital":{
                                          "TimbreFiscaldigital": "",
                                          "FechaTimbrado": "",
                                          "NoCertificadoSAT": "",
                                          "RfcProvCertif": "",
                                          "SelloCFD": "",
                                          "SelloSAT": "",
                                          "UUID": "",
                                          "Version": ""
                                            },
                                    "Pagos": {
                                            "Version": "",
                                            "Pago": [
                                            ]
                                          }
                                  },
                                        
                                    
                                    "Conceptos": {
                                        "Concepto": concepto
                                    },                                                
                                    "Emisor": {
                                        "Nombre": name_emi_dec,
                                        "RegimenFiscal": self.company_id.partner_id.regimen_fiscal_id.code,
                                        "Rfc": rfc_dec
                                    },
                                    "Fecha": fecha,#self.date_done and time.strftime('%Y-%m-%dT%H:%M:%S', time.strptime(str(self.date_done), '%Y-%m-%d %H:%M:%S')),
                                    "Folio": self.name,    
                                    "Exportacion": "01",                   
                                    "LugarExpedicion": self.company_id.codigopostal_sat_id.code,
                                    "Moneda": "XXX",
                                    "NoCertificado": "",
                                    "Receptor": {
                                        "Nombre": name_rec_dec,
                                        "NumRegIdTrib": "",
                                        "RFc": rfc_dec_prov,
                                        "ResidenciaFiscal": "",
                                        "UsoCFDI": 'S01',
                                        "RegimenFiscalReceptor": self.partner_id.regimen_fiscal_id.code,                    
                                        "DomicilioFiscalReceptor": self.partner_id.sat_codigopostal_id.code
                                    },
                                    "Sello": "",
                                    "Serie": self.name,
                                    "Subtotal": "0", 
                                    #"TipoCambio":"",              
                                    "TipoDeComprobante": "T",
                                    "Total": "0",
                                    "Version": "3.3"
                                },
                                "Operacion": "TIMBRAR",
                                "TipoDocumento": "FACTURA"
                            },
                            "login": login
                        }

                        }

        dir = '/home'
        filename = "cartaporte40.json"
        with open(os.path.join(dir, filename), 'w') as file:
            json.dump(cata_porte, file)
        _logger.error('datos: %s', cata_porte)   
        datos_cod = str(cata_porte).encode('utf-8')
        base64_datos = base64.b64encode(datos_cod)
        cadena = ""
        cadena = base64_datos.decode("utf-8")
        cadena_data = cadena
        data = {

               "datos":cadena_data
                

               }

        
        #_logger.error('data: %s', data)
        headers = {'content-type': 'application/json'}        
        res = requests.post(str(url) + "/Timbrar/CFDI", data=json.dumps(data), headers=headers)
        respuesta = json.loads(res.content.decode("utf-8"))
        _logger.error('respuesta: %s', respuesta)
        amount = 0.0
        ad = dict()
        cfdi = dict()
        if respuesta['Codigo'] == 1:
            _logger.error('sello: %s', respuesta['Data']['Timbre']['SelloEmisor'])
            ad['UUID'] = respuesta['Data']['Timbre']['FolioFsical']
            ad['FechaTimbrado'] = self.date_done
            ad['no_certificado'] = respuesta['Data']['Timbre']['NoCertificado']
            ad['cfdi_cadena_original'] = respuesta['Data']['Timbre']['CadenaOriginal']
            ad['Sello'] = respuesta['Data']['Timbre']['SelloSAT']
            ad['pac_timbre'] = respuesta['Data']['Timbre']['CFDIPac']            
            ad['cfdi_cadena_original'] = respuesta['Data']['Timbre']['CadenaOriginal']
            ad['sello'] = respuesta['Data']['Timbre']['SelloEmisor']
            xml_recep = respuesta['Data']['Timbre']['Xml'] 
            ad['state_sat'] = 'validate'
            _logger.error(base64.b64decode(xml_recep))   
                           
            self.write(ad) 
            
            cfdi['type_document'] = "Factura Traslado(Carta Porte)"
            cfdi['fecha_timbrado'] = self.date_done
            cfdi['cfdi_num_certificado'] = self.company_id.serial_number
            cfdi['cfdi_sello'] = respuesta['Data']['Timbre']['SelloEmisor']
            cfdi['cfdi_folio'] = respuesta['Data']['Timbre']['FolioFsical']
            cfdi['cfdi_cadena_original'] = respuesta['Data']['Timbre']['CadenaOriginal']
            cfdi['pac_timbrado'] = respuesta['Data']['Timbre']['CFDIPac']
            cfdi['sello'] = respuesta['Data']['Timbre']['SelloSAT']
            cfdi['certificado'] = respuesta['Data']['Timbre']['NoCertificado']
            cfdi['total_docto'] = 0.0
            cfdi['name'] = self.name
            cfdi['rfc_emisor'] = self.company_id.rfc
            cfdi['rfc_receptor'] = self.partner_id.rfc
            cfdi['codigo_bm'] = self.create_qr_image(respuesta, amount)
            cfdi['pac_timbrado'] = respuesta['Data']['Timbre']['CFDIPac']
            cfdi['currency_id'] = self.sale_id.currency_id.id
            self.env['xmlcfdi'].create(cfdi)         
            self.cfdi_cbb = self.create_qr_image(respuesta, amount)

            xml_dec = base64.decodestring(str.encode(xml_recep))            
            xml_dec= xml_dec.decode("utf-8").replace('\r\n','') 

            attachment_obj = self.env['ir.attachment']   
            
            data_at = {
                        'name': fname_invoice,
                        'datas': base64.encodestring(str.encode(xml_dec)),               
                        'description': 'Archivo XML del Comprobante Fiscal Digital de la factura',
                        'res_model': 'stock.picking',
                        'res_id': self.id,
                        'type': 'binary',                        
            }
            attach = attachment_obj.with_context({}).create(data_at)
            xres = self.do_something_with_xml_attachment(attach)
        else:            
            if respuesta['Codigo'] == 0:
                raise UserError(_("Error de Timbrado:\n\n %s" % respuesta['Data']['Error']['CodigoError']))

    def return_index_floats(self,decimales):
        i = len(decimales) - 1
        indice = 0
        while(i > 0):
            if decimales[i] != '0':
                indice = i
                i = -1
            else:
                i-=1
        return  indice   

    @api.model                     
    def create_qr_image(self, values, amount_total):       
        
        url = "https://verificacfdi.facturaelectronica.sat.gob.mx/default.aspx?"
        UUID = self.UUID
        qr_emisor = self.company_id.rfc   
        qr_receptor = self.partner_id.rfc
        total = "%.6f" % (0.0)
        total_qr = ""
        qr_total_split = total.split('.')        
        decimales = qr_total_split[1]
        index_zero = self.return_index_floats(decimales)
        decimales_res = decimales[0:index_zero+1]
        if decimales_res == '0':
            total_qr = qr_total_split[0]

        else:
            total_qr = qr_total_split[0]+"."+decimales_res
            
        last_8_digits_sello = ""
        
        cfdi_sello =  self.Sello        
        last_8_digits_sello = cfdi_sello[len(cfdi_sello)-8:]         
        qr_string = '%s&id=%s&re=%s&rr=%s&tt=%s&fe=%s'% (url, UUID, qr_emisor, qr_receptor, total_qr, last_8_digits_sello)       
        #try:
        img = qrcode.make(qr_string.encode('utf-8'))
        _logger.error("imagen: %s", img)
        output = io.BytesIO()
        img.save(output, format='JPEG')
        qr_bytes = base64.encodestring(output.getvalue())
        
        return qr_bytes or False 

class figuratransporte(models.Model):
    _name = 'figuratransporte'

    picking_id = fields.Many2one('stock.picking', string='salida')
    figuratrasnporte = fields.Many2one('hr.employee', string='Nombre', domain="[('tipofigura_is', '=', True)]")
    numlicencia = fields.Char(related='figuratrasnporte.numlicencia', string='Numero de licencia')
    rfcfigura = fields.Char(related='figuratrasnporte.rfcfigura', string='RFC')
    tipofigura = fields.Many2one(related='figuratrasnporte.tipofigura', string='Tipo Figura')


class FleetVehicle(models.Model):
    
    _inherit = 'fleet.vehicle'
    
    
    PermSCT = fields.Many2one('c_tipopermiso', string="Permiso SCT")
    NumPermisoSCT = fields.Char('Número de Permiso SCT')
    ConfigVehicular = fields.Many2one('c_configautotransporte', string="Clave Vehicular")
    vehiculo_is = fields.Boolean('Para Carta Porte')
    categoiria_vehiculo = fields.Selection([
        ('vehiculo', 'Vehiculo'),   
        ('remolque', 'Remolque/Semi-Remolque'),                           
        ], string='Categoria de Vehiculo', copy=False, index=True)
    SubTipoRem = fields.Many2one('c_subtiporem', string='Sub-Tipo Remolque')
    remolques_ids = fields.One2many('remolque', 'fleet_id', string="Remolques")
    partner_owner = fields.Many2one('res.partner', string="Propietario", domain="[('is_owner', '=', True)]")
    parte_transporte = fields.Many2one('c_partetransporte', string='Parte Transporte')

    @api.constrains('model_year')
    def _check_año(self):
        for rec in self:
            if rec.model_year:
                if not _estructura_año.match(rec.model_year):
                    raise UserError(_('Error!\nregistrar solo el año'))
class ResPartner(models.Model):    
    _inherit = 'res.partner'

    is_owner = fields.Boolean('Propietario')
    tipofigura = fields.Many2one('c_figuratransporte', string='Tipo Figura')
    

class FleetremolquePicking(models.Model):
    _name = 'remolque_picking'
    picking_id = fields.Many2one('stock.picking', string='Vehiculo')   
    invoice_id = fields.Many2one('account.move', string='Remolques')
    remolque_id = fields.Many2one('fleet.vehicle', string='Remolque', domain="[('categoiria_vehiculo', '=', 'remolque')]")
    SubTipoRem = fields.Many2one(related='remolque_id.SubTipoRem', string='Sub-tipo Remolque')
    license_plate = fields.Char(related='remolque_id.license_plate', string='Placa')

class Fleetremolque(models.Model):
    _name = 'remolque'
    picking_id = fields.Many2one('stock.picking', string='Vehiculo')

    fleet_id = fields.Many2one('fleet.vehicle', string='flota')
    remolque_id = fields.Many2one('fleet.vehicle', string='Remolque', domain="[('categoiria_vehiculo', '=', 'remolque')]")
    SubTipoRem = fields.Many2one(related='remolque_id.SubTipoRem', string='Sub-tipo Remolque')
    license_plate = fields.Char(related='remolque_id.license_plate', string='Placa')

class Mercancias(models.Model):
    _name = 'mercancias'


    stock_picking_id = fields.Many2one('stock.picking', 'Salida')
    #stock_move_id = fields.Many2one('stock.move', 'movimiento')
    product_id = fields.Many2one('product.product', string="Producto")
    product_uom = fields.Many2one(related='product_id.uom_id', string='Unidad de Medida')
    product_qty = fields.Char(string='Cantidad')
    dimensiones = fields.Char('Dimensiones')
    valorproducto = fields.Float('Valor de la mercancía', default=1.0)
    peso = fields.Float('Peso en Kg')
    currency = fields.Many2one('res.currency', string="Moneda", required=False, readonly=True,
        default=lambda self: self.env.user.company_id.currency_id.id)
    materialpeligroso = fields.Selection([('si', 'Sí'),
                                          ('no', 'No')
                                            ], string='Material Peligroso')
    para_cartaporte = fields.Boolean('Para Carta Porte')
    embalaje = fields.Many2one('c_tipoembalaje', string='Embalaje')
    CveMaterialPeligroso = fields.Many2one('c_materialpeligroso', string='Clave Material peligro')
    #DescripEmbalaje = fields.Char('Descripción del Embalaje')

    @api.onchange('product_id')
    def onchange_product(self):       
        
       
        if self.product_id:
            if self.product_id.sat_product_id.MaterialPeligroso == '1':    
                _logger.info('actualiza')           
                self.materialpeligroso = 'si'
                self.stock_picking_id.tipo_seguro_amb = True
            else:
                _logger.info('actualiza2')
                self.materialpeligroso = 'no'
    
          
    @api.constrains('peso')
    def _check_peso(self):
        for rec in self:
            if rec.peso <= 0.0:
                
                raise UserError(_('Error!\nEl valor registrado en la columna PesoEnKg de la tabla de mercancías deben se mayor cero'))


    @api.constrains('dimensiones')
    def _check_dimensiones(self):
        for rec in self:
            if rec.dimensiones:
                if not _estructura_dimenciones.match(rec.dimensiones):
                    raise UserError(_('Error!\nSe debe registrar la longitud, la altura y la anchura en centímetros o en pulgadas, separados dichos valores con una diagonal, i.e. 30/40/30cm'))








