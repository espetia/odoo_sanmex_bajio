# -*- encoding: utf-8 -*-

from odoo import api, fields, models, _, tools

from odoo.exceptions import UserError, RedirectWarning, ValidationError
from odoo.osv import osv, expression
import logging
_logger = logging.getLogger(__name__)



###### Codigos Productos y Servicios ######

class SATProducto(models.Model):
    _name = "sat.producto"
    
    
    code = fields.Char(string="Código", size=8, required=True, index=True, readonly=True)
    name = fields.Text(string="Descripción", required=True, index=True, readonly=True)
    vigencia_inicio = fields.Date(string="Vigencia Inicio", default="2017-08-14", required=True, readonly=True)
    vigencia_fin    = fields.Date(string="Vigencia Fin", readonly=True)
    incluir_iva_trasladado = fields.Char(string="Incluir IVA Trasladado", required=True, readonly=True)
    incluir_ieps_trasladado = fields.Char(string="Incluir IEPS Trasladado", required=True, readonly=True)    
    incluye_complemento = fields.Boolean('Incluye Complemento', readonly=True)
    complemento_que_debe_incluir = fields.Char(string="Complemento", readonly=True)
    franja_fronteriza = fields.Boolean('Estímulo Franja Fronteriza', readonly=True)
    description = fields.Text(string='Palabras similares')
     
    
    _sql_constraints = [
        ('code_unique', 'unique(code)',
         'El Código debe ser único')]
        
    #@api.model
    @api.depends('name', 'code')
    def name_get(self):
        result = []
        for rec in self:
            if rec.name and rec.code:
                name = '[ '+rec.code+' ]' + ' ' + rec.name
                result.append((rec.id, name))
        return result

    
    @api.model
    def name_search(self, name, args=None, operator='ilike', limit=100):
        args = args or []
        domain = []
        if name:
            domain = ['|', ('code', '=ilike', name + '%'), ('name', operator, name)]
            if operator in expression.NEGATIVE_TERM_OPERATORS:
                domain = ['&', '!'] + domain[1:]
        recs = self.search(domain + args, limit=limit)
        return recs.name_get()   


    
###### Unidades de Medida ######
class SATUdM(models.Model):
    _name = "sat.udm"
    
    
    code            = fields.Char(string="Código", size=4, required=True, index=True, readonly=True)
    name            = fields.Char(string="Nombre", required=True, readonly=True)
    description     = fields.Text(string="Descripción", readonly=True)
    vigencia_inicio = fields.Char(string="Vigencia Inicio", required=False, readonly=True)
    vigencia_fin    = fields.Date(string="Vigencia Fin", required=False, readonly=True)
    symbol          = fields.Char(string="Símbolo", readonly=True)
    notes           = fields.Text('Notas', readonly=True)
    
    _sql_constraints = [
        ('code_unique', 'unique(code)',
         'El Código debe ser único')]
        
    #@api.model
    @api.depends('name', 'code')
    def name_get(self):
       result = []
       for rec in self:
            if rec.name and rec.code:
                name = '[ '+rec.code+' ]' + ' ' + rec.name
                result.append((rec.id, name))
       return result

    @api.model
    def name_search(self, name, args=None, operator='ilike', limit=100):
        args = args or []
        domain = []
        if name:
            domain = ['|', ('code', '=ilike', name + '%'), ('name', operator, name)]
            if operator in expression.NEGATIVE_TERM_OPERATORS:
                domain = ['&', '!'] + domain[1:]
        recs = self.search(domain + args, limit=limit)
        return recs.name_get()       


###### Impuestos ######
class SATImpuesto(models.Model):
    _name = "sat.impuesto"
    
    
    code            = fields.Char(string="Código", size=10, required=True)
    name            = fields.Char(string="Nombre", required=True, readonly=True)
    retencion       = fields.Boolean(string="Retención", required=True, readonly=True)
    traslado        = fields.Boolean(string="Traslado", required=True, readonly=True)
    tipo            = fields.Selection([('federal','Federal'),
                                        ('local','Local')],
                                        string="Tipo", help="Aplicación de Impuesto, puede ser Federal o Local", readonly=True, default="federal")
    entidades_donde_aplica = fields.Many2many("res.country.state",string="Entidades donde Aplica")
    
    
    _sql_constraints = [
        ('code_unique', 'unique(code)',
         'El Código debe ser único')]


    #@api.model
    @api.depends('name', 'code')
    def name_get(self):
       result = []
       for rec in self:
            if rec.name and rec.code:
                name = '[ '+rec.code+' ]' + ' ' + rec.name
                result.append((rec.id, name))
       return result

    
    @api.model
    def name_search(self, name, args=None, operator='ilike', limit=100):
        args = args or []
        domain = []
        if name:
            domain = ['|', ('code', '=ilike', name + '%'), ('name', operator, name)]
            if operator in expression.NEGATIVE_TERM_OPERATORS:
                domain = ['&', '!'] + domain[1:]
        recs = self.search(domain + args, limit=limit)
        return recs.name_get()

###### PAISES #########

class ResCountrySatCode(models.Model):
    _name = 'res.country.sat.code'
    _description = 'Codigos de Paises del SAT'
        
    code = fields.Char('Codigo', size=64)
    name = fields.Char('Pais')

    formato_cp      = fields.Char(string="Formato Código Postal")
    formato_registro_tributario = fields.Char(string="Formato Registro Tributario")
    validacion_registro_tributario = fields.Char(string="Validación del Registro de Identidad Tributaria")
    
    _sql_constraints = [
        ('code_unique', 'unique(code)',
         'El Código debe ser único')]    

    #@api.model
    @api.depends('code', 'name')
    def name_get(self):
        result = []
        for rec in self:
            if rec.name and rec.code:
                name = "[ "+rec.code+"] "+rec.name
                result.append((rec.id, name))
        return result

    
    @api.model
    def name_search(self, name, args=None, operator='ilike', limit=100):
        args = args or []
        domain = []
        if name:
            domain = ['|', ('code', '=ilike', name + '%'), ('name', operator, name)]
            if operator in expression.NEGATIVE_TERM_OPERATORS:
                domain = ['&', '!'] + domain[1:]
        recs = self.search(domain + args, limit=limit)
        return recs.name_get()

class res_country(models.Model):
    _name = 'res.country'
    _inherit = 'res.country'
        
    sat_code = fields.Many2one('res.country.sat.code', 'Codigo SAT CE', help='Codigo del PAIS para Comercio Exterior', )
    
    #@api.model
    @api.depends('sat_code', 'name')
    def name_get(self):
        result = []
        for rec in self:
            if rec.name and rec.code:
                code = rec.sat_code.code if rec.sat_code else rec.code
                name = "[ "+code+" ] "+rec.name
                result.append((rec.id, name))
        return result

    
    @api.model
    def name_search(self, name, args=None, operator='ilike', limit=100):
        args = args or []
        domain = []
        if name:
            domain = ['|', '|',('code', '=ilike', name + '%'), ('sat_code.code', '=ilike', name + '%'), ('name', operator, name)]
            if operator in expression.NEGATIVE_TERM_OPERATORS:
                domain = ['&', '!'] + domain[1:]
        recs = self.search(domain + args, limit=limit)
        return recs.name_get()

###### ESTADOS #########

class ResCountryStateSatCode(models.Model):
    _name = 'res.country.state.sat.code'
    _description = 'Codigos de Estados del SAT'
       
    code = fields.Char('Codigo', size=64, required=True)
    name = fields.Char('Nombre Estado', required=True)
    country_sat_code = fields.Char('Codigo Pais SAT', required=False, default='prueba')

    #@api.model
    @api.depends('code', 'name')
    def name_get(self):
        result = []
        for rec in self:
            if rec.name and rec.code:
                code = rec.code
                name = "[ "+code+" ] "+rec.name
                result.append((rec.id, name))
        return result

    
    @api.model
    def name_search(self, name, args=None, operator='ilike', limit=100):
        args = args or []
        domain = []
        if name:
            domain = ['|', ('code', '=ilike', name + '%'), ('name', operator, name)]
            if operator in expression.NEGATIVE_TERM_OPERATORS:
                domain = ['&', '!'] + domain[1:]
        recs = self.search(domain + args, limit=limit)
        return recs.name_get()


class ResCountryState(models.Model):
    _name = 'res.country.state'
    _inherit = 'res.country.state'

    sat_code = fields.Many2one('res.country.state.sat.code', 'Codigo SAT CE', help='Codigo del Estado para Comercio Exterior', )

    @api.onchange('sat_code','country_id')
    def onchange_domain_sat_list(self):
        domain = {}
        if self.country_id:
            state_sat_obj = self.env['res.country.state.sat.code']
            states_ids = state_sat_obj.search([('country_sat_code','=',self.country_id.sat_code.code)])
            if states_ids:
                domain.update(
                    {
                        'sat_code':[('id','in',[x.id for x in states_ids])]
                    })

        if self.sat_code:
            country_sat_obj = self.env['res.country']
            country_ids = country_sat_obj.search([('sat_code.code','=',self.sat_code.country_sat_code)])
            if country_ids:
                domain.update(
                    {
                        'country_id':[('id','in',[x.id for x in country_ids])]
                    })

        if not self.country_id and not self.sat_code:
            state_sat_obj = self.env['res.country.state.sat.code']
            states_ids = state_sat_obj.search([])
            country_sat_obj = self.env['res.country']
            country_ids = country_sat_obj.search([])
            domain.update(
                    {
                        'sat_code':[('id','in',[x.id for x in states_ids])],
                        'country_id':[('id','in',[x.id for x in country_ids])]
                    })

        return {'domain': domain}

###### MUNICIPIOS #########

class ResCountryTownshipSatCode(models.Model):
    _name = 'res.country.township.sat.code'
    _description = 'Codigos de Municipios del SAT'
       
    code = fields.Char('Codigo', size=64)
    name = fields.Char('Nombre Municipio')
    state_sat_code = fields.Char('Codigo Estado SAT')

    #@api.model
    @api.depends('code', 'name')
    def name_get(self):
        result = []
        for rec in self:
            if rec.name and rec.code:
                code = rec.code
                name = "[ "+code+" ] "+rec.name
                result.append((rec.id, name))
        return result

    @api.model
    def name_search(self, name, args=None, operator='ilike', limit=100):
        args = args or []
        domain = []
        if name:
            domain = ['|', ('code', '=ilike', name + '%'), ('name', operator, name)]
            if operator in expression.NEGATIVE_TERM_OPERATORS:
                domain = ['&', '!'] + domain[1:]
        recs = self.search(domain + args, limit=limit)
        return recs.name_get()
    

###### Localidades #########

class ResCountryLocalitySatCode(models.Model):
    _name = 'res.country.locality.sat.code'
    _description = 'Codigos de Localidades del SAT'
        
    code = fields.Char('Codigo', size=64)
    name = fields.Char('Nombre Localidad')
    state_sat_code = fields.Char('Codigo Estado SAT')

    #@api.model
    @api.depends('code', 'name')
    def name_get(self):
        result = []
        for rec in self:
            if rec.name and rec.code:
                code = rec.code
                name = "[ "+code+" ] "+rec.name
                result.append((rec.id, name))
        return result

    @api.model
    def name_search(self, name, args=None, operator='ilike', limit=100):
        args = args or []
        domain = []
        if name:
            domain = ['|', ('code', '=ilike', name + '%'), ('name', operator, name)]
            if operator in expression.NEGATIVE_TERM_OPERATORS:
                domain = ['&', '!'] + domain[1:]
        recs = self.search(domain + args, limit=limit)
        return recs.name_get()
    

###### Codigos Postales #########

class ResCountryZipSatCode(models.Model):
    _name = 'res.country.zip.sat.code'
    _description = 'Codigos de Codigos Postales del SAT'
    _rec_name = 'code' 

        
    code = fields.Char('Codigo', size=64)
    state_sat_code = fields.Char('Codigo Estado SAT')
    township_sat_code = fields.Char('Codigo Municipio SAT')
    locality_sat_code = fields.Char('Codigo Localidad SAT')

    state_sat_code_char = fields.Char('Codigo Estado SAT (CADENA)', size=64)
    township_sat_code_char = fields.Char('Codigo Municipio SAT (CADENA)', size=64)
    locality_sat_code_char = fields.Char('Codigo Localidad SAT (CADENA)', size=64)
    franja_fronteriza = fields.Boolean('Estímulo Franja Fronteriza')

    

###### Colonias #########

class ResColoniaZipSatCode(models.Model):
    _name = 'res.colonia.zip.sat.code'
    _description = 'Codigos de Codigos colonias del SAT'
     
    name = fields.Char('Nombre Colonia',size=256)    
    code = fields.Char('Codigo', size=64)
    #zip_sat_code = fields.Char('Codigo Postal SAT')
    
    zip_sat_code_char = fields.Char('Codigo Postal SAT', size=64)
    
    
    #@api.model
    @api.depends('code', 'name')
    def name_get(self):
        result = []
        for rec in self:
            if rec.name and rec.code:
                code = rec.code
                name = "[ "+code+" ] "+rec.name
                result.append((rec.id, name))
        return result

    @api.model
    def name_search(self, name, args=None, operator='ilike', limit=100):
        args = args or []
        domain = []
        if name:
            domain = ['|', ('code', '=ilike', name + '%'), ('name', operator, name)]
            if operator in expression.NEGATIVE_TERM_OPERATORS:
                domain = ['&', '!'] + domain[1:]
        recs = self.search(domain + args, limit=limit)
        return recs.name_get()

    

######## Aduanas ################

###### Aduanas - c_Aduana ######
class SATAduana(models.Model):
    _name = "sat.aduana"
    
    
    code = fields.Char(string="Clave Aduana", size=64, required=True, index=True)
    name = fields.Text(string="Descripción", required=True, index=True)
    
    _sql_constraints = [
        ('code_unique', 'unique(code)',
         'El Código debe ser único')]
    
    #@api.model
    @api.depends('name', 'code')
    def name_get(self):
        result = []
        for rec in self:
            if rec.code and rec.name:
                name = '[ '+rec.code+' ]' + ' ' + rec.name
                result.append((rec.id, name))
        return result

    
    @api.model
    def name_search(self, name, args=None, operator='ilike', limit=100):
        args = args or []
        domain = []
        if name:
            domain = ['|', ('code', '=ilike', name + '%'), ('name', operator, name)]
            if operator in expression.NEGATIVE_TERM_OPERATORS:
                domain = ['&', '!'] + domain[1:]
        recs = self.search(domain + args, limit=limit)
        return recs.name_get()
   
###### Metodos de Pago ######
class SATMetodoPago(models.Model):
    _name = "sat.metodo.pago"
    
    
    code            = fields.Char(string="Código", size=10, required=True, index=True)
    name            = fields.Char(string="Nombre", required=True)
    
    
    _sql_constraints = [
        ('code_unique', 'unique(code)',
         'El Código debe ser único')]
    
    #@api.model
    @api.depends('name', 'code')
    def name_get(self):
        result = []
        for rec in self:
            if rec.name and rec.code:
                name = '[ '+rec.code+' ]' + ' ' + rec.name
                result.append((rec.id, name))
        return result

    
    @api.model
    def name_search(self, name, args=None, operator='ilike', limit=100):
        args = args or []
        domain = []
        if name:
            domain = ['|', ('code', '=ilike', name + '%'), ('name', operator, name)]
            if operator in expression.NEGATIVE_TERM_OPERATORS:
                domain = ['&', '!'] + domain[1:]
        recs = self.search(domain + args, limit=limit)
        return recs.name_get()

###### Pedimentos Aduanales - c_NumPedimentoAduana ######
class SATPatente(models.Model):
    _name = "sat.patente"    
    
    
    aduana_code = fields.Char(string="Aduana", required=False, index=True)    
    ejercicio = fields.Char(string="Ejercicio", required=False, size=4)
    cantidad = fields.Char(string="Cantidad", required=False, size=6,
                                 help="Solo se pueden usar 6 caracteres numéricos, por ejemplo: 003000")
    
    start_date = fields.Date('Inicio Vigencia', required=False)
    end_date      = fields.Date('Fin Vigencia', required=False)
    name_1            = fields.Char(string="Patente", required=False)

    

    

###### Pedimentos Aduanales ######
class SATPatenteAduanal(models.Model):
    _name = "sat.patente.aduanal"    
    _rec_name = 'code' 

    code      = fields.Char("Patente Aduanal", required=True, size=128 )    
    vigencia_inicio = fields.Date(string="Vigencia Inicio", required=False)
    vigencia_fin    = fields.Date(string="Vigencia Fin", required=False)
    name            = fields.Char('Descripcion', size=128)

class SATclavepedimento(models.Model):
    _name = "sat.clavepedimento"    
    

    code = fields.Char("Clave Pedimento", required=True, size=128 )   
    name = fields.Char('Descripcion', size=128)

class SATTipooperacion(models.Model):
    _name = "sat.tipooperacion"    
    

    code = fields.Char("Clave Tipo de Operación", required=True, size=128 )   
    name = fields.Char('Descripcion', size=128)

class SATmotivotraslado(models.Model):
    _name = "sat.traslado"    
    

    code = fields.Char("Clave Motivo Traslado", required=True, size=128 )   
    name = fields.Char('Descripcion', size=128)

###### Regimen Fiscal ######


class SATRegimenFiscal(models.Model):
    _name = 'sat.regimen.fiscal'
    _description = 'Regimen Fiscal'
    _order = 'name'

    code        = fields.Char(string="Código", size=10, required=True, index=True)
    name        = fields.Char(string='Regimen Fiscal', required=True)
    aplica_persona_fisica = fields.Boolean(string="Aplica Persona Física", default=False, required=True)
    aplica_persona_moral  = fields.Boolean(string="Aplica Persona Moral", default=False, required=True)
    
    
    _sql_constraints = [
        ('code_unique', 'unique(code)',
         'El Código debe ser único')]
    
    #@api.model
    @api.depends('name', 'code')
    def name_get(self):
        result = []
        for rec in self:
            if rec.name and rec.code:
                name = '[ '+rec.code+' ]' + ' ' + rec.name
                result.append((rec.id, name))
        return result

    
    @api.model
    def name_search(self, name, args=None, operator='ilike', limit=100):
        args = args or []
        domain = []
        if name:
            domain = ['|', ('code', '=ilike', name + '%'), ('name', operator, name)]
            if operator in expression.NEGATIVE_TERM_OPERATORS:
                domain = ['&', '!'] + domain[1:]
        recs = self.search(domain + args, limit=limit)
        return recs.name_get()


###### Uso de CFDI ######
class SATUsoCfdi(models.Model):
    _name = 'sat.uso.cfdi'
    _description = 'Uso de CFDI'
    _order = 'name'

    code        = fields.Char(string="Código", size=10, required=True, index=True)
    name        = fields.Char(string='Descripción', required=True)
    aplica_persona_fisica = fields.Boolean(string="Aplica Persona Física", default=False, required=True)
    aplica_persona_moral  = fields.Boolean(string="Aplica Persona Moral", default=False, required=True)
    RegimenFiscalReceptor = fields.Char('Régimen Fiscal Receptor', readonly=True)
    
    _sql_constraints = [
        ('code_unique', 'unique(code)',
         'El Código debe ser único')]
    
    #@api.model
    @api.depends('name', 'code')
    def name_get(self):
        result = []
        for rec in self:
            if rec.name and rec.code:
                name = '[ '+rec.code+' ]' + ' ' + rec.name
                result.append((rec.id, name))
        return result

    
    @api.model
    def name_search(self, name, args=None, operator='ilike', limit=100):
        args = args or []
        domain = []
        if name:
            domain = ['|', ('code', '=ilike', name + '%'), ('name', operator, name)]
            if operator in expression.NEGATIVE_TERM_OPERATORS:
                domain = ['&', '!'] + domain[1:]
        recs = self.search(domain + args, limit=limit)
        return recs.name_get()

###### Tipo de Comprobante ######
class SATTipoCombroante(models.Model):
    _name = 'sat.tipo.comprobante'
    _description = 'Tipo de Comprobante'
    _order = 'name'

    code        = fields.Char(string="Código", size=10, required=True, index=True)
    name        = fields.Char(string='Descripción', required=True)
    
    _sql_constraints = [
        ('code_unique', 'unique(code)',
         'El Código debe ser único')]

    #@api.model
    @api.depends('name', 'code')
    def name_get(self):
        result = []
        for rec in self:
            if rec.name and rec.code:
                name = '[ '+rec.code+' ]' + ' ' + rec.name
                result.append((rec.id, name))
        return result

    
    @api.model
    def name_search(self, name, args=None, operator='ilike', limit=100):
        args = args or []
        domain = []
        if name:
            domain = ['|', ('code', '=ilike', name + '%'), ('name', operator, name)]
            if operator in expression.NEGATIVE_TERM_OPERATORS:
                domain = ['&', '!'] + domain[1:]
        recs = self.search(domain + args, limit=limit)
        return recs.name_get()


###### Tipo de Comprobante ######
class SATCfdiRelacionado(models.Model):
    _name = 'sat.tipo.relacion.cfdi'
    _description = 'Tipo de Relacion CFDI'
    _order = 'code'

    code        = fields.Char(string="Código", size=10, required=True, index=True)
    name        = fields.Char(string='Descripción', required=True)
    
    _sql_constraints = [
        ('code_unique', 'unique(code)',
         'El Código debe ser único')]
        
    #@api.model
    @api.depends('name', 'code')
    def name_get(self):
        result = []
        for rec in self:
            if rec.name and rec.code:
                name = '[ '+rec.code+' ]' + ' ' + rec.name
                result.append((rec.id, name))
        return result

    
    @api.model
    def name_search(self, name, args=None, operator='ilike', limit=100):
        args = args or []
        domain = []
        if name:
            domain = ['|', ('code', '=ilike', name + '%'), ('name', operator, name)]
            if operator in expression.NEGATIVE_TERM_OPERATORS:
                domain = ['&', '!'] + domain[1:]
        recs = self.search(domain + args, limit=limit)
        return recs.name_get()


    
    
###### Fracción Arancelaria - c_FraccionArancelaria ######
class SATFraccionArancelaria(models.Model):
    _name = "sat.arancel"
    
    
    code = fields.Char(string="Clave", size=64, required=True, index=True)
    name = fields.Text(string="Descripción", required=True, index=True)
    vigencia_inicio = fields.Date(string="Vigencia Inicio", required=True, default='2016-10-01')
    vigencia_fin    = fields.Date(string="Vigencia Fin")
    criterio        = fields.Char(string="Criterio")
    unidad_de_medida= fields.Char(string='Unidad de Medida')
    impuesto_importacion = fields.Char(string="Impuesto Importación")
    impuesto_exportacion = fields.Char(string="Impuesto Exportación")
    
    _sql_constraints = [
        ('code_unique', 'unique(code)',
         'El Código debe ser único')]
    
    #@api.model
    @api.depends('name', 'code')
    def name_get(self):
        result = []
        for rec in self:
            if rec.code and rec.name:
                name = '[ '+rec.code+' ]' + ' ' + rec.name
                result.append((rec.id, name))
        return result

    
    @api.model
    def name_search(self, name, args=None, operator='ilike', limit=100):
        args = args or []
        domain = []
        if name:
            domain = ['|', ('code', '=ilike', name + '%'), ('name', operator, name)]
            if operator in expression.NEGATIVE_TERM_OPERATORS:
                domain = ['&', '!'] + domain[1:]
        recs = self.search(domain + args, limit=limit)
        return recs.name_get()  

class pay_method(models.Model):
    _name = 'pay.method'

    code        = fields.Char(string='Clave SAT', required=True)
    name        = fields.Char(string='Forma de Pago', size=128, required=True)
    

    bancarizado = fields.Char(string="Bancarizado", required=True)
    num_operacion = fields.Char(string="No. Operación", required=True)
    
    rfc_del_emisor_cuenta_ordenante = fields.Char(string="RFC del Emisor de la Cuenta Ordenante", required=True)
    
    cuenta_ordenante = fields.Char(string="Cuenta Ordenante", required=True)
    patron_cuenta_ordenante = fields.Char(string="Patrón para Cuenta Ordenante")
    
    rfc_del_emisor_cuenta_beneficiario = fields.Char(string="RFC del Emisor Cuenta de Beneficiario", required=True)
    
    cuenta_beneficiario = fields.Char(string="Cuenta Beneficiario", required=True)
    
    patron_cuenta_beneficiario = fields.Char(string="Patrón para Cuenta Beneficiario")
    
    
    tipo_cadena_pago = fields.Char(string="Tipo Cadena Pago", required=True)
    
    banco_emisor_obligatorio_extranjero = fields.Boolean(string="Requerir Nombre Banco Emisor",
                                                        help="Nombre del Banco emisor de la cuenta ordenante en caso de extranjero")
    
    _sql_constraints = [
        ('name_uniq', 'unique(name)', 'El nombre de la Forma de Pago debe ser único !'),
        ('code_uniq', 'unique(code)', 'La clave de la Forma de Pago debe ser único !'),
    ]    
    
    
    @api.model
    def name_search(self, name, args=None, operator='ilike', limit=100):
        args = args or []
        domain = []
        if name:
            domain = ['|', ('code', '=ilike', name + '%'), ('name', operator, name)]
            if operator in expression.NEGATIVE_TERM_OPERATORS:
                domain = ['&'] + domain
        accounts = self.search(domain + args, limit=limit)
        return accounts.name_get()
    

    #@api.model
    @api.depends('name', 'code')
    def name_get(self):
        result = []
        for x in self:
            if x.code and x.name:
                name = '[ '+x.code + ' ] ' + x.name
                result.append((x.id, name))
        return result        


class EaccountPaymentMethod(models.Model):
    _name = 'eaccount.payment.methods'

    code        = fields.Char(string='Clave SAT', required=True)
    name        = fields.Char(string='Forma de Pago', size=128, required=True)
    
    
    _sql_constraints = [
        ('name_uniq', 'unique(name)', 'El nombre de la Forma de Pago debe ser único !'),
        ('code_uniq', 'unique(code)', 'La clave de la Forma de Pago debe ser único !'),
    ]    
    


class res_currency_fit(models.Model):
    _name = 'eaccount.currency'

    code            = fields.Char(string="Código", size=10, required=True, index=True)
    name            = fields.Char(string="Descripción", required=True)
    decimales       = fields.Integer(string="Decimales", default=2, required=True)
    porcentaje_variacion = fields.Float(string="Porcentaje de Variación", required=True, default=5.0,
                                       help="Usar valores entre 0 y 100 con 2 puntos decimales")
    
    
    _sql_constraints = [
        ('code_unique', 'unique(code)',
         'El Código debe ser único')]
    
    #@api.model
    @api.depends('name', 'code')
    def name_get(self):
        result = []
        for rec in self:
            if rec.name and rec.code:
                name = '[ '+rec.code+' ]' + ' ' + rec.name
                result.append((rec.id, name))
        return result

    
    @api.model
    def name_search(self, name, args=None, operator='ilike', limit=100):
        args = args or []
        domain = []
        if name:
            domain = ['|', ('code', '=ilike', name + '%'), ('name', operator, name)]
            if operator in expression.NEGATIVE_TERM_OPERATORS:
                domain = ['&', '!'] + domain[1:]
        recs = self.search(domain + args, limit=limit)
        return recs.name_get()  
    

   



class res_currency_sat(models.Model):
    _inherit = 'res.currency'
    
    sat_currency_id = fields.Many2one('eaccount.currency', string='Código del SAT')

class account_journal_types(models.Model):
    _name = 'account.journal.types'
    
    
    name = fields.Char(string='Nombre', size=120, required=True)
    code = fields.Integer(string='Código', size=20, required=True)

class sat_account_code(models.Model):
    _name = 'sat.account.code'
    

    key  = fields.Char(string='Código agrupador', size=10, required=True)
    name = fields.Char(string='Descripción', size=250, required=True)

    #@api.model
    @api.depends('name', 'key')
    def name_get(self):
        result = []
        for rec in self:
            if rec.name and rec.key:
                name = '[ '+rec.key+' ]' + ' ' + rec.name
                result.append((rec.id, name))
        return result

    @api.model
    def name_search(self, name, args=None, operator='ilike', limit=100):
        args = args or []
        domain = []
        if name:
            domain = ['|', ('key', '=ilike', name + '%'), ('name', operator, name)]
            if operator in expression.NEGATIVE_TERM_OPERATORS:
                domain = ['&', '!'] + domain[1:]
        recs = self.search(domain + args, limit=limit)
        return recs.name_get()
        
class sat_tasa_cuota(models.Model):
    _name = 'sat.tasa.cuota'

    name = fields.Char('Rango o Fijo')
    value_min = fields.Float('Valor Minimo')
    value_max = fields.Float('Valor Maximo')
    taxes = fields.Char('Impuesto')
    factor = fields.Char('Factor')
    traslado = fields.Boolean('Traslado')
    retencion = fields.Boolean('Retención')
    fecha_start = fields.Date('Fecha inicio de Vigencia')
    fecha_end = fields.Date('Fecha Fin de Vigencia')


    #@api.model
    @api.depends('name', 'value_max', 'taxes')
    def name_get(self):
       result = []
       for rec in self:
            if rec.name and rec.taxes:
                _logger.error('Valor maximo: %s', rec.value_max)
                name = rec.name + '-' + rec.taxes + '( ' + str(rec.value_max) + ')'
                _logger.error('Nombre: %s', name)
                result.append((rec.id, name))
       return result
       
   

class sat_tipofactor(models.Model):
    _name = 'sat.tipofactor'    

    
    name = fields.Char(string='Tipo Factor', size=250, required=True)

class pacs_timbres(models.Model):
    _name = 'pac.timbres'    

    
    name = fields.Char(string='Clave', size=250, required=True)
    nombre_pac = fields.Char(string='Nombre Pac', required=True)


    #@api.model
    @api.depends('name', 'nombre_pac')
    def name_get(self):
        result = []
        for rec in self:
            if rec.name and rec.nombre_pac:
                name = '[ '+rec.name+' ]' + ' ' + rec.nombre_pac
                result.append((rec.id, name))
        return result

class TipoContribuyente(models.Model):
    _name = 'contribuyente'    

    
    code = fields.Char(string='Clave', size=250, required=True)
    name = fields.Char(string='Tipo contribuyente', required=True)
    rfc = fields.Char('RFC Asignado')


    #@api.model
    @api.depends('code', 'name')
    def name_get(self):
        result = []
        for rec in self:
            if rec.code and rec.name:
                name = '[ '+rec.code+' ]' + ' ' + rec.name
                result.append((rec.id, name))
        return result

#####catalogos 4.0#######
class c_MesesSat(models.Model):
    _name = "sat.meses"

    c_Meses = fields.Char('Clave', readonly=True)
    Descripcion = fields.Char('Descripción', readonly=True)
    #Fechainiciodevigencia = fileds.Date('Fecha inicio de vigencia', readonly=True)

    _sql_constraints = [
        ('code_unique', 'unique(c_Meses)',
         'El Código debe ser único')]
        
   
    @api.depends('Descripcion', 'c_Meses')
    def name_get(self):
        result = []
        for rec in self:
            if rec.Descripcion and rec.c_Meses:
                name = '[ '+rec.c_Meses+' ]' + ' ' + rec.Descripcion
                result.append((rec.id, name))
        return result

    
    @api.model
    def name_search(self, name, args=None, operator='ilike', limit=100):
        args = args or []
        domain = []
        if name:
            domain = ['|', ('c_Meses', '=ilike', name + '%'), ('Descripcion', operator, name)]
            if operator in expression.NEGATIVE_TERM_OPERATORS:
                domain = ['&', '!'] + domain[1:]
        recs = self.search(domain + args, limit=limit)
        return recs.name_get()   

class c_Periodicidad(models.Model):
    _name = "sat.periodicidad"

    c_Periodicidad = fields.Char('Clave', readonly=True)
    Descripcion = fields.Char('Descripción', readonly=True)

    _sql_constraints = [
        ('code_unique', 'unique(c_Periodicidad)',
         'El Código debe ser único')]
        
   
    @api.depends('Descripcion', 'c_Periodicidad')
    def name_get(self):
        result = []
        for rec in self:
            if rec.Descripcion and rec.c_Periodicidad:
                name = '[ '+rec.c_Periodicidad+' ]' + ' ' + rec.Descripcion
                result.append((rec.id, name))
        return result

    
    @api.model
    def name_search(self, name, args=None, operator='ilike', limit=100):
        args = args or []
        domain = []
        if name:
            domain = ['|', ('c_Periodicidad', '=ilike', name + '%'), ('Descripcion', operator, name)]
            if operator in expression.NEGATIVE_TERM_OPERATORS:
                domain = ['&', '!'] + domain[1:]
        recs = self.search(domain + args, limit=limit)
        return recs.name_get()   

class c_ObjetoImp(models.Model):
    _name = "sat.objetoimp"

    c_ObjetoImp = fields.Char('Clave', readonly=True)
    Descripcion = fields.Char('Descripción', readonly=True)

    _sql_constraints = [
        ('code_unique', 'unique(c_ObjetoImp)',
         'El Código debe ser único')]
        
   
    @api.depends('Descripcion', 'c_ObjetoImp')
    def name_get(self):
        result = []
        for rec in self:
            if rec.Descripcion and rec.c_ObjetoImp:
                name = '[ '+rec.c_ObjetoImp+' ]' + ' ' + rec.Descripcion
                result.append((rec.id, name))
        return result

    
    @api.model
    def name_search(self, name, args=None, operator='ilike', limit=100):
        args = args or []
        domain = []
        if name:
            domain = ['|', ('c_ObjetoImp', '=ilike', name + '%'), ('Descripcion', operator, name)]
            if operator in expression.NEGATIVE_TERM_OPERATORS:
                domain = ['&', '!'] + domain[1:]
        recs = self.search(domain + args, limit=limit)
        return recs.name_get()      


class c_Exportacion(models.Model):
    _name = "sat.exportacion"

    c_Exportacion = fields.Char('Clave', readonly=True)
    Descripcion = fields.Char('Descripción', readonly=True)

    _sql_constraints = [
        ('code_unique', 'unique(c_Exportacion)',
         'El Código debe ser único')]
        
   
    @api.depends('Descripcion', 'c_Exportacion')
    def name_get(self):
        result = []
        for rec in self:
            if rec.Descripcion and rec.c_Exportacion:
                name = '[ '+rec.c_Exportacion+' ]' + ' ' + rec.Descripcion
                result.append((rec.id, name))
        return result

    
    @api.model
    def name_search(self, name, args=None, operator='ilike', limit=100):
        args = args or []
        domain = []
        if name:
            domain = ['|', ('c_Exportacion', '=ilike', name + '%'), ('Descripcion', operator, name)]
            if operator in expression.NEGATIVE_TERM_OPERATORS:
                domain = ['&', '!'] + domain[1:]
        recs = self.search(domain + args, limit=limit)
        return recs.name_get()

