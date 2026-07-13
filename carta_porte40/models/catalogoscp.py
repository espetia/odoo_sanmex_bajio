from odoo import api, fields, models, _, tools

from odoo.exceptions import UserError, RedirectWarning, ValidationError
from odoo.osv import osv, expression
import logging
_logger = logging.getLogger(__name__)



######c_ConfigMaritima ######

class c_ConfigMaritima(models.Model):
    _name = "configura.maritima"
    
    
    Clave = fields.Char(string="Clave", size=16, required=True, index=True, readonly=True)
    Descripcion = fields.Text(string="Descripción", required=True, index=True, readonly=True)
    FechaInicioVigencia = fields.Date(string="Vigencia Inicio", default="2017-08-14", required=True, readonly=True)
    FechaFinVigencia = fields.Date(string="Vigencia Fin", readonly=True)
   
     
    
    _sql_constraints = [
        ('Clave_unique', 'unique(Clave)',
         'El Código debe ser único')]
        
    #@api.model
    @api.depends('Descripcion', 'Clave')
    def name_get(self):
        result = []
        for rec in self:
            if rec.Descripcion and rec.Clave:
                name = '[ '+rec.Clave+' ]' + ' ' + rec.Descripcion
                result.append((rec.id, name))
        return result

    
    @api.model
    def name_search(self, name, args=None, operator='ilike', limit=100):
        args = args or []
        domain = []
        if name:
            domain = ['|', ('Clave', '=ilike', name + '%'), ('Descripcion', operator, name)]
            if operator in expression.NEGATIVE_TERM_OPERATORS:
                domain = ['&', '!'] + domain[1:]
        recs = self.search(domain + args, limit=limit)
        return recs.name_get()   

######c_CveTransporte ######

class c_CveTransporte(models.Model):
    _name = "c_cvetransporte"
    
    
    ClaveTransporte = fields.Char(string="Clave", size=16, required=True, index=True, readonly=True)
    Descripcion = fields.Text(string="Descripción", required=True, index=True, readonly=True)
    FechaInicioVigencia = fields.Date(string="Vigencia Inicio", default="2017-08-14", required=True, readonly=True)
    FechaFinVigencia = fields.Date(string="Vigencia Fin", readonly=True)
   
     
    
    _sql_constraints = [
        ('Clave_unique', 'unique(ClaveTransporte)',
         'El Código debe ser único')]
        
    #@api.model
    @api.depends('Descripcion', 'ClaveTransporte')
    def name_get(self):
        result = []
        for rec in self:
            if rec.Descripcion and rec.ClaveTransporte:
                name = '[ '+rec.ClaveTransporte+' ]' + ' ' + rec.Descripcion
                result.append((rec.id, name))
        return result

    
    @api.model
    def name_search(self, name, args=None, operator='ilike', limit=100):
        args = args or []
        domain = []
        if name:
            domain = ['|', ('ClaveTransporte', '=ilike', name + '%'), ('Descripcion', operator, name)]
            if operator in expression.NEGATIVE_TERM_OPERATORS:
                domain = ['&', '!'] + domain[1:]
        recs = self.search(domain + args, limit=limit)
        return recs.name_get()   
######c_TipoEstacion ######

class c_TipoEstacion(models.Model):
    _name = "c_tipoestacion"
    
    
    Clave = fields.Char(string="Clave", size=16, required=True, index=True, readonly=True)
    Descripcion = fields.Text(string="Descripción", required=True, index=True, readonly=True)
    FechaInicioVigencia = fields.Date(string="Vigencia Inicio", default="2017-08-14", required=True, readonly=True)
    FechaFinVigencia = fields.Date(string="Vigencia Fin", readonly=True)
    ClaveTransporte = fields.Char(string="Clave Transporte", required=True, index=True, readonly=True)
     
    
    _sql_constraints = [
        ('Clave_unique', 'unique(Clave)',
         'El Código debe ser único')]
        
    #@api.model
    @api.depends('Descripcion', 'Clave')
    def name_get(self):
        result = []
        for rec in self:
            if rec.Descripcion and rec.Clave:
                name = '[ '+rec.Clave+' ]' + ' ' + rec.Descripcion
                result.append((rec.id, name))
        return result

    
    @api.model
    def name_search(self, name, args=None, operator='ilike', limit=100):
        args = args or []
        domain = []
        if name:
            domain = ['|', ('Clave', '=ilike', name + '%'), ('Descripcion', operator, name)]
            if operator in expression.NEGATIVE_TERM_OPERATORS:
                domain = ['&', '!'] + domain[1:]
        recs = self.search(domain + args, limit=limit)
        return recs.name_get()   

######c_Estaciones ######
class c_Estaciones(models.Model):
    _name = "c_estaciones"
    
    
    Clave = fields.Char(string="Clave", size=16, required=True, index=True, readonly=True)
    Descripcion = fields.Text(string="Descripción", required=True, index=True, readonly=True)
    FechaInicioVigencia = fields.Date(string="Vigencia Inicio", default="2017-08-14", required=True, readonly=True)
    FechaFinVigencia = fields.Date(string="Vigencia Fin", readonly=True)
    ClaveTransporte = fields.Char(string="Clave Transporte", required=True, index=True, readonly=True)
    Nacionalidad = fields.Char(string="Nacionalidad", required=True, index=True, readonly=True)
    DesignadorIATA = fields.Char(string="Designador IATA", required=True, index=True, readonly=True)
    LineaFerrea = fields.Char(string="Linea Ferrea", required=True, index=True, readonly=True)
    
    _sql_constraints = [
        ('Clave_unique', 'unique(Clave)',
         'El Código debe ser único')]
        
    #@api.model
    @api.depends('Descripcion', 'Clave')
    def name_get(self):
        result = []
        for rec in self:
            if rec.Descripcion and rec.Clave:
                name = '[ '+rec.Clave+' ]' + ' ' + rec.Descripcion
                result.append((rec.id, name))
        return result

    
    @api.model
    def name_search(self, name, args=None, operator='ilike', limit=100):
        args = args or []
        domain = []
        if name:
            domain = ['|', ('Clave', '=ilike', name + '%'), ('Descripcion', operator, name)]
            if operator in expression.NEGATIVE_TERM_OPERATORS:
                domain = ['&', '!'] + domain[1:]
        recs = self.search(domain + args, limit=limit)
        return recs.name_get() 

######c_ClaveUnidadPeso ######
class c_ClaveUnidadPeso(models.Model):
    _name = "c_claveunidadpeso"
    
    
    Clave = fields.Char(string="Clave", size=16, required=True, index=True, readonly=True)
    Nombre = fields.Char(string="Nombre", required=True, index=True, readonly=True)
    Descripcion = fields.Text(string="Descripción", required=True, index=True, readonly=True)
    FechaInicioVigencia = fields.Date(string="Vigencia Inicio", default="2017-08-14", required=True, readonly=True)
    FechaFinVigencia = fields.Date(string="Vigencia Fin", readonly=True)
    Nota = fields.Char(string="Nota", required=True, index=True, readonly=True)
    Simbolo = fields.Char(string="Simbolo", required=True, index=True, readonly=True)
    Bandera = fields.Char(string="Bandera", required=True, index=True, readonly=True)
   
    
    _sql_constraints = [
        ('Clave_unique', 'unique(Clave)',
         'El Código debe ser único')]
        
    #@api.model
    @api.depends('Nombre', 'Clave')
    def name_get(self):
        result = []
        for rec in self:
            if rec.Nombre and rec.Clave:
                name = '[ '+rec.Clave+' ]' + ' ' + rec.Nombre
                result.append((rec.id, name))
        return result

    
    @api.model
    def name_search(self, name, args=None, operator='ilike', limit=100):
        args = args or []
        domain = []
        if name:
            domain = ['|', ('Clave', '=ilike', name + '%'), ('Nombre', operator, name)]
            if operator in expression.NEGATIVE_TERM_OPERATORS:
                domain = ['&', '!'] + domain[1:]
        recs = self.search(domain + args, limit=limit)
        return recs.name_get() 

######c_MaterialPeligroso ######
class c_MaterialPeligroso(models.Model):
    _name = "c_materialpeligroso"
    
    
    Clave = fields.Char(string="Clave", size=16, required=True, index=True, readonly=True)   
    Descripcion = fields.Text(string="Descripción", required=True, index=True, readonly=True)
    FechaInicioVigencia = fields.Date(string="Vigencia Inicio", default="2017-08-14", required=True, readonly=True)
    FechaFinVigencia = fields.Date(string="Vigencia Fin", readonly=True)
    ClaseODiv = fields.Char(string="Clase o Div.", required=True, index=True, readonly=True)
    PeligroSecundario = fields.Char(string="Peligro Secundario", required=True, index=True, readonly=True)
    NombreTecnico = fields.Char(string="Nombre Tecnico", required=True, index=True, readonly=True)
   
    
    _sql_constraints = [
        ('Clave_unique', 'unique(Clave)',
         'El Código debe ser único')]
        
    #@api.model
    @api.depends('Descripcion', 'Clave')
    def name_get(self):
        result = []
        for rec in self:
            if rec.Descripcion and rec.Clave:
                name = '[ '+rec.Clave+' ]' + ' ' + rec.Descripcion
                result.append((rec.id, name))
        return result

    
    @api.model
    def name_search(self, name, args=None, operator='ilike', limit=100):
        args = args or []
        domain = []
        if name:
            domain = ['|', ('Clave', '=ilike', name + '%'), ('Descripcion', operator, name)]
            if operator in expression.NEGATIVE_TERM_OPERATORS:
                domain = ['&', '!'] + domain[1:]
        recs = self.search(domain + args, limit=limit)
        return recs.name_get() 

######c_TipoEmbalaje ######
class c_TipoEmbalaje(models.Model):
    _name = "c_tipoembalaje"
    
    
    CalveDesignacion = fields.Char(string="Clave de designación", size=16, required=True, index=True, readonly=True)   
    Descripcion = fields.Text(string="Descripción", required=True, index=True, readonly=True)
    FechaInicioVigencia = fields.Date(string="Vigencia Inicio", default="2017-08-14", required=True, readonly=True)
    FechaFinVigencia = fields.Date(string="Vigencia Fin", readonly=True)
    
   
    
    _sql_constraints = [
        ('Clave_unique', 'unique(Clave)',
         'El Código debe ser único')]
        
    #@api.model
    @api.depends('Descripcion', 'CalveDesignacion')
    def name_get(self):
        result = []
        for rec in self:
            if rec.Descripcion and rec.CalveDesignacion:
                name = '[ '+rec.CalveDesignacion+' ]' + ' ' + rec.Descripcion
                result.append((rec.id, name))
        return result

    
    @api.model
    def name_search(self, name, args=None, operator='ilike', limit=100):
        args = args or []
        domain = []
        if name:
            domain = ['|', ('CalveDesignacion', '=ilike', name + '%'), ('Descripcion', operator, name)]
            if operator in expression.NEGATIVE_TERM_OPERATORS:
                domain = ['&', '!'] + domain[1:]
        recs = self.search(domain + args, limit=limit)
        return recs.name_get() 

######c_TipoPermiso ######
class c_TipoPermiso(models.Model):
    _name = "c_tipopermiso"
    
    
    Clave = fields.Char(string="Clave", size=16, required=True, index=True, readonly=True)   
    Descripcion = fields.Text(string="Descripción", required=True, index=True, readonly=True)
    FechaInicioVigencia = fields.Date(string="Vigencia Inicio", default="2017-08-14", required=True, readonly=True)
    FechaFinVigencia = fields.Date(string="Vigencia Fin", readonly=True)
    ClaveTransporte = fields.Char(string="Clase de Transporte", required=True, index=True, readonly=True)
    
   
    
    _sql_constraints = [
        ('Clave_unique', 'unique(Clave)',
         'El Código debe ser único')]
        
    #@api.model
    @api.depends('Descripcion', 'Clave')
    def name_get(self):
        result = []
        for rec in self:
            if rec.Descripcion and rec.Clave:
                name = '[ '+rec.Clave+' ]' + ' ' + rec.Descripcion
                result.append((rec.id, name))
        return result

    
    @api.model
    def name_search(self, name, args=None, operator='ilike', limit=100):
        args = args or []
        domain = []
        if name:
            domain = ['|', ('Clave', '=ilike', name + '%'), ('Descripcion', operator, name)]
            if operator in expression.NEGATIVE_TERM_OPERATORS:
                domain = ['&', '!'] + domain[1:]
        recs = self.search(domain + args, limit=limit)
        return recs.name_get()

######c_ParteTransporte ######
class c_ParteTransporte(models.Model):
    _name = "c_partetransporte"
    
    
    Clave = fields.Char(string="Clave", size=16, required=True, index=True, readonly=True)   
    Descripcion = fields.Text(string="Descripción", required=True, index=True, readonly=True)
    FechaInicioVigencia = fields.Date(string="Vigencia Inicio", default="2017-08-14", required=True, readonly=True)
    FechaFinVigencia = fields.Date(string="Vigencia Fin", readonly=True)
    
    
   
    
    _sql_constraints = [
        ('Clave_unique', 'unique(Clave)',
         'El Código debe ser único')]
        
    #@api.model
    @api.depends('Descripcion', 'Clave')
    def name_get(self):
        result = []
        for rec in self:
            if rec.Descripcion and rec.Clave:
                name = '[ '+rec.Clave+' ]' + ' ' + rec.Descripcion
                result.append((rec.id, name))
        return result

    
    @api.model
    def name_search(self, name, args=None, operator='ilike', limit=100):
        args = args or []
        domain = []
        if name:
            domain = ['|', ('Clave', '=ilike', name + '%'), ('Descripcion', operator, name)]
            if operator in expression.NEGATIVE_TERM_OPERATORS:
                domain = ['&', '!'] + domain[1:]
        recs = self.search(domain + args, limit=limit)
        return recs.name_get()

######c_FiguraTransporte ######
class c_FiguraTransporte(models.Model):
    _name = "c_figuratransporte"
    
    
    Clave = fields.Char(string="Clave", size=16, required=True, index=True, readonly=True)   
    Descripcion = fields.Text(string="Descripción", required=True, index=True, readonly=True)
    FechaInicioVigencia = fields.Date(string="Vigencia Inicio", default="2017-08-14", required=True, readonly=True)
    FechaFinVigencia = fields.Date(string="Vigencia Fin", readonly=True)
    
    
   
    
    _sql_constraints = [
        ('Clave_unique', 'unique(Clave)',
         'El Código debe ser único')]
        
    #@api.model
    @api.depends('Descripcion', 'Clave')
    def name_get(self):
        result = []
        for rec in self:
            if rec.Descripcion and rec.Clave:
                name = '[ '+rec.Clave+' ]' + ' ' + rec.Descripcion
                result.append((rec.id, name))
        return result

    
    @api.model
    def name_search(self, name, args=None, operator='ilike', limit=100):
        args = args or []
        domain = []
        if name:
            domain = ['|', ('Clave', '=ilike', name + '%'), ('Descripcion', operator, name)]
            if operator in expression.NEGATIVE_TERM_OPERATORS:
                domain = ['&', '!'] + domain[1:]
        recs = self.search(domain + args, limit=limit)
        return recs.name_get()

######c_ConfigAutoTransporte ######
class c_ConfigAutoTransporte(models.Model):
    _name = "c_configautotransporte"
    
    
    Clave = fields.Char(string="Clave", size=16, required=True, index=True, readonly=True)   
    Descripcion = fields.Text(string="Descripción", required=True, index=True, readonly=True)
    FechaInicioVigencia = fields.Date(string="Vigencia Inicio", default="2017-08-14", required=True, readonly=True)
    FechaFinVigencia = fields.Date(string="Vigencia Fin", readonly=True)
    NumeroEjes = fields.Char(string="Número de Ejes", required=True, index=True, readonly=True)
    NumeroLlantas = fields.Char(string="Número de Llantas", required=True, index=True, readonly=True)
    Remolque = fields.Char(string="Remolque", required=True, index=True, readonly=True)
    
   
    
    _sql_constraints = [
        ('Clave_unique', 'unique(Clave)',
         'El Código debe ser único')]
        
    #@api.model
    @api.depends('Descripcion', 'Clave')
    def name_get(self):
        result = []
        for rec in self:
            if rec.Descripcion and rec.Clave:
                name = '[ '+rec.Clave+' ]' + ' ' + rec.Descripcion
                result.append((rec.id, name))
        return result

    
    @api.model
    def name_search(self, name, args=None, operator='ilike', limit=100):
        args = args or []
        domain = []
        if name:
            domain = ['|', ('Clave', '=ilike', name + '%'), ('Descripcion', operator, name)]
            if operator in expression.NEGATIVE_TERM_OPERATORS:
                domain = ['&', '!'] + domain[1:]
        recs = self.search(domain + args, limit=limit)
        return recs.name_get()

######c_SubTipoRem ######
class c_SubTipoRem(models.Model):
    _name = "c_subtiporem"
    
    
    Clave = fields.Char(string="Clave", size=16, required=True, index=True, readonly=True)   
    FechaInicioVigencia = fields.Date(string="Vigencia Inicio", default="2017-08-14", required=True, readonly=True)
    FechaFinVigencia = fields.Date(string="Vigencia Fin", readonly=True)
    RemolqueSemiremolque = fields.Char(string="Remolque o Semirremolque", required=True, index=True, readonly=True)
   
   
    
    _sql_constraints = [
        ('Clave_unique', 'unique(Clave)',
         'El Código debe ser único')]

    @api.depends('Descripcion', 'Clave')
    def name_get(self):
        result = []
        for rec in self:
            if rec.Clave:
                name = '[ '+rec.Clave+' ]' + ' ' + rec.RemolqueSemiremolque
                result.append((rec.id, name))
        return result

    
    @api.model
    def name_search(self, name, args=None, operator='ilike', limit=100):
        args = args or []
        domain = []
        if name:
            domain = ['|', ('Clave', '=ilike', name + '%'), ('Descripcion', operator, name)]
            if operator in expression.NEGATIVE_TERM_OPERATORS:
                domain = ['&', '!'] + domain[1:]
        recs = self.search(domain + args, limit=limit)
        return recs.name_get() 
        
######c_ClaveTipoCarga ######
class c_ClaveTipoCarga(models.Model):
    _name = "c_clavetipocarga"
    
    
    Clave = fields.Char(string="Clave", size=16, required=True, index=True, readonly=True)   
    Descripcion = fields.Text(string="Descripción", required=True, index=True, readonly=True)
    FechaInicioVigencia = fields.Date(string="Vigencia Inicio", default="2017-08-14", required=True, readonly=True)
    FechaFinVigencia = fields.Date(string="Vigencia Fin", readonly=True)
   
    
   
    
    _sql_constraints = [
        ('Clave_unique', 'unique(Clave)',
         'El Código debe ser único')]
        
    #@api.model
    @api.depends('Descripcion', 'Clave')
    def name_get(self):
        result = []
        for rec in self:
            if rec.Descripcion and rec.Clave:
                name = '[ '+rec.Clave+' ]' + ' ' + rec.Descripcion
                result.append((rec.id, name))
        return result

    
    @api.model
    def name_search(self, name, args=None, operator='ilike', limit=100):
        args = args or []
        domain = []
        if name:
            domain = ['|', ('Clave', '=ilike', name + '%'), ('Descripcion', operator, name)]
            if operator in expression.NEGATIVE_TERM_OPERATORS:
                domain = ['&', '!'] + domain[1:]
        recs = self.search(domain + args, limit=limit)
        return recs.name_get() 

######c_ContenedorMaritimo ######
class c_ContenedorMaritimo(models.Model):
    _name = "c_contenedormaritimo"
    
    
    Clave = fields.Char(string="Clave", size=16, required=True, index=True, readonly=True)   
    Descripcion = fields.Text(string="Descripción", required=True, index=True, readonly=True)
    FechaInicioVigencia = fields.Date(string="Vigencia Inicio", default="2017-08-14", required=True, readonly=True)
    FechaFinVigencia = fields.Date(string="Vigencia Fin", readonly=True)
   
    
   
    
    _sql_constraints = [
        ('Clave_unique', 'unique(Clave)',
         'El Código debe ser único')]
        
    #@api.model
    @api.depends('Descripcion', 'Clave')
    def name_get(self):
        result = []
        for rec in self:
            if rec.Descripcion and rec.Clave:
                name = '[ '+rec.Clave+' ]' + ' ' + rec.Descripcion
                result.append((rec.id, name))
        return result

    
    @api.model
    def name_search(self, name, args=None, operator='ilike', limit=100):
        args = args or []
        domain = []
        if name:
            domain = ['|', ('Clave', '=ilike', name + '%'), ('Descripcion', operator, name)]
            if operator in expression.NEGATIVE_TERM_OPERATORS:
                domain = ['&', '!'] + domain[1:]
        recs = self.search(domain + args, limit=limit)
        return recs.name_get()   

######c_NumAutorizacionNaviero ######
class c_NumAutorizacionNaviero(models.Model):
    _name = "c_numautorizacionnaviero"
    
    
    NumeroAutorizacion = fields.Char(string="Número de Autorización", size=16, required=True, index=True, readonly=True)       
    FechaInicioVigencia = fields.Date(string="Vigencia Inicio", default="2017-08-14", required=True, readonly=True)
    FechaFinVigencia = fields.Date(string="Vigencia Fin", readonly=True)
   
    
   
    
    _sql_constraints = [
        ('NumeroAutorizacion_unique', 'unique(NumeroAutorizacion)',
         'El Código debe ser único')]

######c_CodigoTransporteAereo ######
class c_CodigoTransporteAereo(models.Model):
    _name = "c_codigotransporteaereo"
    
    
    Clave = fields.Char(string="Clave", size=16, required=True, index=True, readonly=True)   
    Nacionalidad = fields.Text(string="Nacionalidad", required=True, index=True, readonly=True)
    NombreAerolinea = fields.Text(string="Nombre Aerolinea", required=True, index=True, readonly=True)
    DesignadorOACI = fields.Text(string="Designador OACI", required=True, index=True, readonly=True)
    FechaInicioVigencia = fields.Date(string="Vigencia Inicio", default="2017-08-14", required=True, readonly=True)
    FechaFinVigencia = fields.Date(string="Vigencia Fin", readonly=True)
   
    
   
    
    _sql_constraints = [
        ('Clave_unique', 'unique(Clave)',
         'El Código debe ser único')]
        
           
######c_TipoDeServicio ######
class c_TipoDeServicio(models.Model):
    _name = "c_tipodeservicio"
    
    
    Clave = fields.Char(string="Clave", size=16, required=True, index=True, readonly=True)   
    Descripcion = fields.Text(string="Descripción", required=True, index=True, readonly=True)
    Contenedor = fields.Text(string="Contenedor", required=True, index=True, readonly=True)
    FechaInicioVigencia = fields.Date(string="Vigencia Inicio", default="2017-08-14", required=True, readonly=True)
    FechaFinVigencia = fields.Date(string="Vigencia Fin", readonly=True)
   
    
   
    
    _sql_constraints = [
        ('Clave_unique', 'unique(Clave)',
         'El Código debe ser único')]
        
    #@api.model
    @api.depends('Descripcion', 'Clave')
    def name_get(self):
        result = []
        for rec in self:
            if rec.Descripcion and rec.Clave:
                Descripcion = '[ '+rec.Clave+' ]' + ' ' + rec.Descripcion
                result.append((rec.id, name))
        return result

    
    @api.model
    def name_search(self, name, args=None, operator='ilike', limit=100):
        args = args or []
        domain = []
        if name:
            domain = ['|', ('Clave', '=ilike', name + '%'), ('Descripcion', operator, name)]
            if operator in expression.NEGATIVE_TERM_OPERATORS:
                domain = ['&', '!'] + domain[1:]
        recs = self.search(domain + args, limit=limit)
        return recs.name_get()  

######c_DerechosDePaso ######
class c_DerechosDePaso(models.Model):
    _name = "c_derechosdepaso"
    
    
    Clave = fields.Char(string="Clave", size=16, required=True, index=True, readonly=True)   
    DerechoDePaso = fields.Text(string="Derecho De Paso", required=True, index=True, readonly=True)
    Entre = fields.Text(string="Entre", required=True, index=True, readonly=True)
    Hasta = fields.Text(string="Hasta", required=True, index=True, readonly=True)
    OtorgaRecibe = fields.Text(string="Otorga/Recibe", required=True, index=True, readonly=True)
    Concesionario = fields.Text(string="Concesionario", required=True, index=True, readonly=True)   
    FechaInicioVigencia = fields.Date(string="Vigencia Inicio", default="2017-08-14", required=True, readonly=True)
    FechaFinVigencia = fields.Date(string="Vigencia Fin", readonly=True)
   
    
   
    
    _sql_constraints = [
        ('Clave_unique', 'unique(Clave)',
         'El Código debe ser único')]

######c_TipoCarro ######
class c_TipoCarro(models.Model):
    _name = "c_tipocarro"
    
    
    Clave = fields.Char(string="Clave", size=16, required=True, index=True, readonly=True)   
    TipoCarro = fields.Text(string="Tipo de Carro", required=True, index=True, readonly=True)
    Contenedor = fields.Text(string="Contenedor", required=True, index=True, readonly=True)
    FechaInicioVigencia = fields.Date(string="Vigencia Inicio", default="2017-08-14", required=True, readonly=True)
    FechaFinVigencia = fields.Date(string="Vigencia Fin", readonly=True)
   
    
   
    
    _sql_constraints = [
        ('Clave_unique', 'unique(Clave)',
         'El Código debe ser único')]

######c_Contenedor ######
class c_Contenedor(models.Model):
    _name = "c_contenedor"
    
    
    Clave = fields.Char(string="Clave", size=16, required=True, index=True, readonly=True)   
    Descripcion = fields.Text(string="Descripción", required=True, index=True, readonly=True)
    TipoContenedor = fields.Text(string="Tipo de Contenedor", required=True, index=True, readonly=True)
    FechaInicioVigencia = fields.Date(string="Vigencia Inicio", default="2017-08-14", required=True, readonly=True)
    FechaFinVigencia = fields.Date(string="Vigencia Fin", readonly=True)
   
    
   
    
    _sql_constraints = [
        ('Clave_unique', 'unique(Clave)',
         'El Código debe ser único')]
        
######c_TipoDeTrafico ######
class c_TipoDeTrafico(models.Model):
    _name = "c_tipodetrafico"
    
    
    Clave = fields.Char(string="Clave", size=16, required=True, index=True, readonly=True)   
    Descripcion = fields.Text(string="Descripción", required=True, index=True, readonly=True)    
    FechaInicioVigencia = fields.Date(string="Vigencia Inicio", default="2017-08-14", required=True, readonly=True)
    FechaFinVigencia = fields.Date(string="Vigencia Fin", readonly=True)
   
    
   
    
    _sql_constraints = [
        ('Clave_unique', 'unique(Clave)',
         'El Código debe ser único')]
        
    #@api.model
    @api.depends('Descripcion', 'Clave')
    def name_get(self):
        result = []
        for rec in self:
            if rec.Descripcion and rec.Clave:
                name = '[ '+rec.Clave+' ]' + ' ' + rec.Descripcion
                result.append((rec.id, name))
        return result

    
    @api.model
    def name_search(self, name, args=None, operator='ilike', limit=100):
        args = args or []
        domain = []
        if name:
            domain = ['|', ('Clave', '=ilike', name + '%'), ('Descripcion', operator, name)]
            if operator in expression.NEGATIVE_TERM_OPERATORS:
                domain = ['&', '!'] + domain[1:]
        recs = self.search(domain + args, limit=limit)
        return recs.name_get()    

class SATProducto(models.Model):
    _inherit = "sat.producto"


    MaterialPeligroso = fields.Char('Material Peligroso', required=True, index=True, readonly=True)

class c_seguros(models.Model):
    _name = "cat.seguros"

    codigo = fields.Char('Clave', required=True)
    name = fields.Char('Aseguradora')
    tipo_seguro = fields.Selection([('AseguraRespCivil', 'Responsabilidad Civil'),
                                    ('AseguraMedAmbiente', 'Medio Ambiente'),
                                    ('AseguraCarga', 'De Carga')], string='Tipo de Póliza')
    polizarespcivil = fields.Char('Número de Póliza')
    polizamedioambiente = fields.Char('Número de Póliza')
    polizacarga = fields.Char('Número de Póliza')
    state = fields.Selection([('vigente', 'Vigente'),
                              ('vencido', 'Vencido')], string='Estado', default='vigente')
    fecha_caducidad = fields.Date('Fecha de Vigencia')


    _sql_constraints = [
        ('codigo_unique', 'unique(codigo)',
         'El Código debe ser único')]
        
    #@api.model
    @api.depends('name', 'codigo')
    def name_get(self):
        result = []
        for rec in self:
            if rec.name and rec.codigo:
                name = '[ '+rec.codigo+' ]' + ' ' + rec.name
                result.append((rec.id, name))
        return result

    
    @api.model
    def name_search(self, name, args=None, operator='ilike', limit=100):
        args = args or []
        domain = []
        if name:
            domain = ['|', ('codigo', '=ilike', name + '%'), ('name', operator, name)]
            if operator in expression.NEGATIVE_TERM_OPERATORS:
                domain = ['&', '!'] + domain[1:]
        recs = self.search(domain + args, limit=limit)
        return recs.name_get()    

    @api.model
    def time_out_update(self, cron=False):
        _logger.info('ejecutano vigencia')
        records = self.search([('state', 'in', ['vigente']),('fecha_caducidad', '<=', fields.Date.today())])
        if records:
            records.write({'state': 'vencido'})
