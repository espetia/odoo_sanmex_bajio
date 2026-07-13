# -*- encoding: utf-8 -*-

from odoo import api, fields, models, _
from odoo.exceptions import UserError, ValidationError
from datetime import datetime
import time
import logging
_logger = logging.getLogger(__name__)

class Declaraciones_sat(models.Model):
    _name = 'declaraciones.sat'

    ESTADOS = [
        ('draft', "Generada"),
        ('done', "Enviada")]

    name = fields.Char("Folio Interno", default=lambda self: _('New'), readonly=True)
    fecha_creacion = fields.Datetime('Fecha de creación', default=datetime.now(), readonly=True)
    fecha_envio = fields.Datetime('Fecha de Envio', readonly=True)
    periodo_declaracion = fields.Char('Periodo Presentado', readonly=True)
    año_fiscal = fields.Char('Año Fiscal Presentado', readonly=True)
    archivo_generado = fields.Char('Declaración', readonly=True)
    state = fields.Selection(ESTADOS, string="Estado", default='draft')
    user_id = fields.Many2one('res.users', string='Usuario', readonly=True)    
    presentadas_ids = fields.One2many('declaracion.presentada', 'id_declaracion', string="Declaraciones Presentadas")

    @api.model
    def create(self, vals):
        
       
        vals['name'] = self.env['ir.sequence'].next_by_code('declaraciones_sat') or _('New')

        result = super(Declaraciones_sat, self).create(vals)
        return result

    @api.model
    def presentar_declaracion(self):
        data = dict()
        if self.presentadas_ids:
            data['id_declaracion'] = self.id
            data['tipo_declaracion'] = "Complementaria"
            self.env['declaracion.presentada'].create(data)
            self.fecha_envio = datetime.now()
            self.state = 'done'
            
        else:
            data['id_declaracion'] = self.id
            data['tipo_declaracion'] = "Normal"
            self.env['declaracion.presentada'].create(data)
            self.fecha_envio = datetime.now()
            self.state = 'done'       
           
        return True

class Declaraciones_Presentadas_sat(models.Model):
    _name = 'declaracion.presentada'

    id_declaracion = fields.Many2one('declaraciones.sat', "Folio de Declaración", readonly=True)
    name = fields.Char("Folio Interno", default=lambda self: _('New'), readonly=True)   
    tipo_declaracion = fields.Char('Tipo', readonly=True)
    fecha_recepcion = fields.Datetime('Fecha de Recepción')
    folio_recepcion = fields.Char('Folio de Recepción')
    archivo_adj = fields.Binary('Adjuntos')

    @api.model
    def create(self, vals):       
       
        vals['name'] = self.env['ir.sequence'].next_by_code('declaraciones_presentada_sat') or _('New')

        result = super(Declaraciones_Presentadas_sat, self).create(vals)
        return result



class catalogo_cuentas(models.Model):
    _name = 'catalogo.cuentas'
    
    account_id    = fields.Many2one('account.account', string='Cuenta Contable', required=True)
    account_code  = fields.Char(string='Código', size=64, required=True)
    order_code    = fields.Char(string='Orden', size=128, required=True)
    account_name  = fields.Char(string='Descripción', size=128, required=True)
    account_level = fields.Integer(string='Nivel', required=True)
    company_name  = fields.Char(string='Nombre Compañía', size=128, required=True)
    parent_id     = fields.Many2one('account.account', string='Cuenta Padre', required=False)
    parent_code   = fields.Char(string='Código Padre', size=64, required=False)
    account_nature= fields.Char(string='Naturaleza', size=1, required=True)
    account_type  = fields.Char(string='Tipo Cuenta', size=128, required=True)
    sat_account_code = fields.Char(string='Código SAT', size=64, required=False)
    sat_account_name = fields.Char(string='Descripción SAT', size=128, required=False)
    
    _order = "order_code, account_code"
    
    
class catalogo_cuentas_wizard(models.TransientModel):
    _name = "catalogo.cuentas.wizard"
    _description = "Generador de Catálogo de Cuentas"

    chart_account_id  = fields.Many2one('account.account', string='Catálogo de Cuentas', 
                                        default=lambda self: self.env['account.account'].search([('parent_id','=',False),('company_id','=',self.env.user.company_id.id)], limit=1),
                                        help='Seleccione Catálogo de Cuentas...', required=True, 
                                        domain = [('parent_id','=',False)])
    
    
    @api.model
    def get_info(self):
        for params in self:
            sql = """
-- Funcion que devuelve los IDs de las cuentas hijo de la cuenta especificada
CREATE OR REPLACE FUNCTION f_account_child_ids(account_id integer)
RETURNS TABLE(id integer) AS
$$

WITH RECURSIVE account_ids(id) AS (
    SELECT id FROM account_account WHERE parent_id = $1
  UNION ALL
    SELECT cuentas.id FROM account_ids, account_account cuentas
    WHERE cuentas.parent_id = account_ids.id
    )
SELECT id FROM account_ids 
union
select $1 id
order by id;
$$ LANGUAGE 'sql';


-- Funcion que devuelve los IDs de las cuentas hijo de la cuenta de consolidacion
CREATE OR REPLACE FUNCTION f_account_child_consol_ids(x_account_id integer)
RETURNS TABLE(id integer) AS
$BODY$
DECLARE
    _cursor CURSOR FOR 
        SELECT parent_id from account_account_consol_rel where child_id in (select f_account_child_ids(x_account_id));
    _result record;
BEGIN
    drop table if exists hesatec_consol_ids;
    create table hesatec_consol_ids(f_account_child_ids integer);

    FOR _record IN _cursor
    LOOP
        insert into hesatec_consol_ids
        select f_account_child_ids(_record.parent_id);
    END LOOP;

    return query
    select * from hesatec_consol_ids;
END
$BODY$
LANGUAGE 'plpgsql' ;


CREATE OR REPLACE FUNCTION f_get_mx_account_account_struct
(x_account_id integer, x_uid integer)
RETURNS boolean
AS
$BODY$
DECLARE
    _cursor2 CURSOR FOR 
        SELECT  id, create_uid, create_date, account_id, account_code, 
            order_code, account_name, account_level, company_name, parent_id, parent_code,
            account_nature
        from catalogo_cuentas
        where account_type='consolidation'
        order by order_code;
    _result2 record;	

BEGIN
    --RAISE NOTICE 'Inicio del Script...';
    delete from catalogo_cuentas;
    -- Creamos el plan contable de la holding
    insert into catalogo_cuentas 
            (id, create_uid, create_date, account_id, account_code, 
            order_code, account_name, account_level, 
            company_name, parent_id, parent_code, account_nature, account_type, sat_account_code, sat_account_name)            
    select  account.id, x_uid::integer create_uid, account.create_date, account.id account_id, account.code account_code, 
        account.code::varchar(1000) order_code, 
        account.name account_name, account.level account_level,
        company.name company_name, account_parent.id parent_id, account_parent.code parent_code,
        case 
        when account.in_debt then 'D'
        when account.in_cred then 'A'
	end::char(1) account_nature, account.internal_type account_type,
	sat.key sat_account_code, sat.name sat_account_name
    from account_account account
	left join account_account account_parent on account_parent.id=account.parent_id and account_parent.parent_id is not null
        inner join res_company company on company.id = account.company_id
        inner join sat_account_code sat on sat.id=account.sat_code_id
        
    where account.id in (select id from f_account_child_ids(x_account_id))
	;--and account.xml_report;

    
    -- Agregamos las cuentas consolidadas con sus hijos
    FOR _record2 IN _cursor2
    LOOP
        
        insert into catalogo_cuentas
        (id, create_uid, create_date, account_id, account_code, 
            order_code, account_name, account_level, 
            company_name, parent_id, parent_code, account_nature, account_type,  sat_account_code, sat_account_name)
        select  account.id, x_uid::integer create_uid, account.create_date, account.id account_id, account.code account_code, 
        (_record2.account_code || ' - ' || account.code)::varchar(1000) order_code,
        account.name account_name, _record2.account_level + 1,
        company.name company_name, _record2.parent_id, _record2.parent_code,
        case
        when account.in_debt then 'D'
        when account.in_cred then 'A'
        end::char(1)  account_nature,
        account.internal_type account_type,
	   sat.key sat_account_code, sat.name sat_account_name
        from account_account account
            inner join res_company company on company.id = account.company_id
            inner join sat_account_code sat on sat.id=account.sat_code_id
        where account.id in (select id from f_account_child_ids(_record2.id) union all select id from f_account_child_consol_ids(_record2.id))
        and account.id != _record2.id;-- and account.xml_report;
            
        
    END LOOP;
	
	return True;
END
$BODY$
LANGUAGE 'plpgsql';

select * from f_get_mx_account_account_struct(%s, %s); """ % (params.chart_account_id.id, self._uid)
            self._cr.execute(sql)
            data = list(filter(None, map(lambda x:x[0], self._cr.fetchall())))
            if not data[0]:
                raise UserError(_('Error en script!\n\nNo se pudo generar el Catálogo de Cuentas, por favor verifique su configuración y vuelva a intentarlo'))

            
            return self.env['catalogo.cuentas'].search([('sat_account_code','!=',False)])
            
    
    