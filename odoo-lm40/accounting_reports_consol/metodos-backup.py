# -*- encoding: utf-8 -*-
###########################################################################
#    Module Writen to OpenERP, Open Source Management Solution
#
#    Copyright (c) 2014 Argil Consulting - http://www.argil.mx
############################################################################
#    Coded by: Israel Cruz Argil (israel.cruz@argil.mx)
############################################################################
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Affero General Public License as
#    published by the Free Software Foundation, either version 3 of the
#    License, or (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Affero General Public License for more details.
#
#    You should have received a copy of the GNU Affero General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################

from odoo.osv import expression, osv
from odoo.tools.float_utils import float_round as round
from odoo.tools import DEFAULT_SERVER_DATETIME_FORMAT
from odoo.exceptions import UserError, ValidationError
from odoo import api, fields, models, _
import odoo.addons.decimal_precision as dp


class AccountMonthlyBalanceWizard(models.TransientModel):
    _inherit = "account.monthly_balance_wizard"
        
    @api.multi
    def get_info(self):
                
        context = dict(self._context.copy() or {})

        data = context and context.get('active_ids', []) or []

        if self.chart_account_id and self.chart_account_id.id:
            

            sql1 = """
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

-------------------------------------------------------
---- Funcion para obtener los datos base de la balanza
-------------------------------------------------------
drop function if exists f_get_mx_account_monthly_balance_base
(x_period_id integer);

drop function if exists f_get_mx_account_monthly_balance_base
(x_account_id integer, x_period_id integer);

drop function if exists f_get_mx_account_monthly_balance_base
(x_account_id integer, x_period_id integer, x_partner_breakdown boolean);

drop function if exists f_get_mx_account_monthly_balance_base
(x_account_id integer, x_period_id integer, x_partner_breakdown boolean, x_uid integer);

drop function if exists f_get_mx_account_monthly_balance
(x_account_id integer, x_period_id integer, x_partner_breakdown boolean, x_uid integer);


CREATE OR REPLACE FUNCTION f_get_mx_account_monthly_balance
(x_account_id integer, x_period_id integer, x_partner_breakdown boolean, x_uid integer)
RETURNS boolean
AS
$BODY$
DECLARE
    _cursor2 CURSOR FOR 
        SELECT  id, create_uid, create_date, account_id, account_code, 
            order_code, account_name, account_level, account_type, parent_id,
            account_user_type, partner_breakdown
        from balanza_mensual
        where account_type='consolidation'
        order by order_code;
    _result2 record;


    _cursor3 CURSOR FOR 
        SELECT  id, create_uid, create_date, account_id, account_code, 
            order_code, account_name, account_level, account_type,
            account_user_type, partner_breakdown
        from balanza_mensual
        where account_type not in ('view','consolidation')
        order by order_code;
    _result3 record;

    _cursor4 CURSOR FOR 
        SELECT  id, create_uid, create_date, account_id, account_code, account_sign, period_name, period_id,
            order_code, account_name, account_level, account_type, create_date, 
            account_user_type, partner_breakdown, company_name
        from balanza_mensual
        where partner_breakdown and not (initial_balance=0.0 and debit=0.0 and credit=0.0)
        order by order_code;
    _result4 record;

    _cursor5 CURSOR FOR 
        SELECT  id, account_id, account_code, account_name
        from balanza_mensual
        where account_type in ('view','consolidation') and partner_id is null
        order by account_level desc;
    _result5 record;

    _period_name varchar(20);
    _period_flag_00 boolean;
    _period_month integer;
    _period_fiscalyear varchar(20);

BEGIN
    --RAISE NOTICE 'Inicio del Script...';
    select date_part('month', period.date_start) into _period_month from account_period period where period.id=x_period_id;
    --RAISE NOTICE 'Period Month: %', _period_month;
    select period.name into _period_name from account_period period where period.id=x_period_id;
    
    drop table if exists period_ids;
    create table period_ids as
    select ap.id  from account_period ap 
    inner join account_fiscalyear afy on afy.id=ap.fiscalyear_id
    where ap.name=_period_name;
    
    drop table if exists period_ids2;
    create table period_ids2 as
    select ap.id
    from account_period ap 
    where date_stop = (select date_start from account_period where id=x_period_id)
    union all
    select ap.id
    from account_period ap 
    where date_stop < (select date_start from account_period where id=x_period_id)
    ;
    --and ap.fiscalyear_id in (select af1.id from account_fiscalyear af1 where af1.name in 
    --                (select af2.name from account_fiscalyear af2 where af2.id=(select ap2.fiscalyear_id from account_period ap2 where ap2.name=_period_name limit 1)))
    --                ;


    --RAISE NOTICE 'Period Name: %', _period_name;
    select ((select count(id) from account_period 
            where id in 
            (select id from account_period where fiscalyear_id=(select fiscalyear_id from account_period where id=x_period_id))
            and name ilike '00%') > 0) into _period_flag_00;

    --RAISE NOTICE 'Period Flag 00: %', _period_flag_00;
    select name into _period_fiscalyear  from account_fiscalyear where id in (select fiscalyear_id from account_period period where period.id=x_period_id);
    --RAISE NOTICE 'Period Fiscalyear ID: %', _period_fiscalyear;

    drop table if exists balanza_mensual;
    -- Creamos el plan contable de la holding
    create table balanza_mensual as
    select  account.id, x_uid::integer create_uid, account.create_date, account.id account_id, account.code account_code, 
        account.code::varchar(1000) order_code, 
        account.name account_name, account.level account_level,
        account.internal_type account_type,
        acc_type.name account_user_type, account.partner_breakdown, false moves, _period_name as period_name,
        0.0::float initial_balance, 0.0::float debit,
        0.0::float credit, 0.0::float balance, 0.0::float ending_balance,
        company.name company_name, account.parent_id,
        --'Acreedora'::varchar(10) account_nature, 
        case account.sign
            when 1 then 'Deudora'
            else 'Acreedora'
        end::varchar(10) account_nature,        
        False::boolean from_partner_breakdown, null::varchar(250) partner_name, null::integer partner_id, account.sign account_sign,
        x_period_id::integer period_id
    from account_account account
        inner join res_company company on company.id = account.company_id
        inner join account_account_type acc_type on acc_type.id=account.user_type_id
    where account.id in (select id from f_account_child_ids(x_account_id));-- union all select id from f_account_child_consol_ids(x_account_id));


    -- Agregamos las cuentas consolidadas con sus hijos
    FOR _record2 IN _cursor2
    LOOP
        
        insert into balanza_mensual
        (id, create_uid, create_date, account_id, account_code, 
            order_code, account_name, account_level, account_type, account_user_type, 
            partner_breakdown, moves, period_name,
            initial_balance, debit, credit, balance, ending_balance,
            company_name, parent_id, account_sign, account_nature, from_partner_breakdown, period_id)
        select  account.id, x_uid::integer create_uid, account.create_date, account.id account_id, account.code account_code, 
        (_record2.account_code || ' - ' || account.code)::varchar(1000) order_code,
        account.name account_name, _record2.account_level + 1,
        account.internal_type account_type, 
        acc_type.name account_user_type, account.partner_breakdown, false moves, _period_name as period_name,
        0.0::float initial_balance, 0.0::float debit,
        0.0::float credit, 0.0::float balance, 0.0::float ending_balance,
        company.name company_name, _record2.parent_id, account.sign account_sign, 
        case account.sign
            when 1 then 'Deudora'
            else 'Acreedora'
        end::varchar(10) account_nature, False::boolean from_partner_breakdown,
        period.id period_id
        from account_account account
            inner join res_company company on company.id = account.company_id
            inner join account_account_type acc_type on acc_type.id=account.user_type_id
            inner join account_period period on account.company_id=period.company_id and period.name=_period_name
        where account.id in (select id from f_account_child_ids(_record2.id) union all select id from f_account_child_consol_ids(_record2.id))
        and account.id != _record2.id;
            
        
    END LOOP;

    --- Copiamos la tabla account_move_line con los movimientos del periodo de la balanza.
    drop table if exists argil_account_move_line;
    
    create table argil_account_move_line as
    select ml.id, ml.account_id, ml.period_id, ml.journal_id, ml.partner_id, ml.debit, ml.credit
    from account_move_line ml
        inner join account_move am on am.id=ml.move_id and am.state='posted'
    where ml.period_id in (select id from period_ids union all select pp2.id from period_ids2 pp2);
    
    create index argil_account_move_line_index2 on argil_account_move_line(account_id, period_id, partner_id);
    ---


    -- Obtenemos los saldos de las cuentas
    FOR _record3 IN _cursor3
    LOOP
        --RAISE NOTICE 'Account: % => %', _record3.account_code,_record3.account_name;
        
        update balanza_mensual
        set 
            initial_balance =
            (
            select COALESCE(sum(line.debit), 0.00) -  COALESCE(sum(line.credit), 0.00)
            from argil_account_move_line line
                inner join account_journal journal on line.journal_id=journal.id --and 
                --(CASE WHEN _period_month = 1 and not _period_flag_00 THEN journal.type <> 'situation' ELSE 1=1 END)
            where --line.state='valid' and
                line.account_id = _record3.id -- in (select f_account_child_ids(_record3.id) union all select f_account_child_consol_ids(_record3.id))
            and line.period_id in (select pp2.id from period_ids2 pp2)
                             --    in 
                             --   (select xperiodo.id from account_period xperiodo 
                             --   where xperiodo.fiscalyear_id in (select id from account_fiscalyear where name = _period_fiscalyear)
                             --   and xperiodo.name < _period_name
                             --   )
            )::float,
            
        debit = (select COALESCE(sum(line.debit), 0.00) 
            from argil_account_move_line line
                inner join account_journal journal on line.journal_id=journal.id --and  journal.type <> 'situation'
            where --line.state='valid' and
                line.account_id = _record3.id --  in (select f_account_child_ids(_record3.id) union all select f_account_child_consol_ids(_record3.id))
            and line.period_id in (select id from period_ids)
                                -- in (select id from account_period where name = _period_name)
                                )::float,
        credit = (select COALESCE(sum(line.credit), 0.00) 
            from argil_account_move_line line
                inner join account_journal journal on line.journal_id=journal.id --and  journal.type <> 'situation'
            where --line.state='valid' and
                line.account_id = _record3.id --  in (select f_account_child_ids(_record3.id) union all select f_account_child_consol_ids(_record3.id))
            and line.period_id in (select id from period_ids)
                                --in (select id from account_period where name = _period_name)
                                )::float/*,
        period_id = (select distinct line.period_id
                from argil_account_move_line line
                inner join account_journal journal on line.journal_id=journal.id --and  journal.type <> 'situation'
                 where --line.state='valid'  and
                     line.account_id = _record3.id --  in (select f_account_child_ids(_record3.id) union all select f_account_child_consol_ids(_record3.id))
                 and line.period_id in (select id from period_ids)
                                    --in (select id from account_period where name = _period_name)
                 limit 1)
        */
        
        where balanza_mensual.id=_record3.id;

        END LOOP;


    IF x_partner_breakdown THEN
        -----------------------------------------------------
        -- Obtenemos los saldos de las cuentas desglosadas por empresa
        FOR _record4 IN _cursor4
        LOOP

            --RAISE NOTICE 'Account: % => %', _record4.account_code,_record4.account_name;


            insert into balanza_mensual
            (id, create_uid, create_date, account_id, account_code, period_id,
                order_code, account_name, account_level, account_type, account_user_type, 
                account_sign, partner_breakdown, period_name, company_name, partner_id, from_partner_breakdown,
                initial_balance, debit, credit
                )
            
            select 
            (_record4.id * 10000 + line.partner_id) id, x_uid::integer, _record4.create_date, _record4.id, _record4.account_code, _record4.period_id,
            _record4.order_code, _record4.account_name, _record4.account_level + 1, _record4.account_type, _record4.account_user_type, 
            _record4.account_sign, _record4.partner_breakdown, _record4.period_name, _record4.company_name, line.partner_id, True,
            
                --initial_balance =
                (
                select COALESCE(sum(xline.debit), 0.00) -  COALESCE(sum(xline.credit), 0.00)
                from argil_account_move_line xline
                    inner join account_journal xjournal on xline.journal_id=xjournal.id --and 
                    --(CASE WHEN _period_month = 1 and not _period_flag_00 THEN xjournal.type <> 'situation' ELSE 1=1 END)
                where --xline.state='valid' and
                    xline.account_id = _record4.id
                and xline.partner_id=line.partner_id
                and xline.period_id in (select pp2.id from period_ids2 pp2)
                            --(select xperiodo.id from account_period xperiodo 
                            --where xperiodo.fiscalyear_id in (select id from account_fiscalyear where name = _period_fiscalyear)
                            --and xperiodo.name < _period_name
                            --)
                )::float,
                
                COALESCE(sum(line.debit), 0.00)::float,
                COALESCE(sum(line.credit), 0.00)::float
                from argil_account_move_line line
                    inner join account_journal journal on line.journal_id=journal.id --and  journal.type <> 'situation'
                where --line.state='valid' and
                    line.account_id = _record4.id
                    and line.partner_id is not null
                and line.period_id in (select id from period_ids) --(select id from account_period where name = _period_name)
                group by _record4.id, _record4.account_code, _record4.order_code,
                _record4.account_name, _record4.account_level + 1, _record4.account_type, _record4.account_user_type,
                _record4.partner_breakdown, _record4.period_name, _record4.company_name, line.partner_id;


        ------------
        ------------
        
            insert into balanza_mensual
            (id, create_uid, create_date, account_id, account_code, period_id,
                order_code, account_name, account_level, account_type, account_user_type, 
                account_sign, partner_breakdown, period_name, company_name, debit, credit, 
                partner_id, from_partner_breakdown, initial_balance
                )
            
            select 
            (_record4.id * 10000 + xline.partner_id) id, x_uid::integer, _record4.create_date, _record4.id, _record4.account_code, _record4.period_id,
            _record4.order_code, _record4.account_name, _record4.account_level + 1, _record4.account_type, _record4.account_user_type, 
            _record4.account_sign, _record4.partner_breakdown, _record4.period_name, _record4.company_name, 0.0, 0.0,
            
            xline.partner_id, True,
            (COALESCE(sum(xline.debit), 0.00) -  COALESCE(sum(xline.credit), 0.00))::float
            from argil_account_move_line xline
                inner join account_journal xjournal on xline.journal_id=xjournal.id --and 
                --(CASE WHEN _period_month = 1 and not _period_flag_00 THEN xjournal.type <> 'situation' ELSE 1=1 END)
            where --xline.state='valid' and
                xline.account_id = _record4.id
            and xline.partner_id not in 
                (select distinct line.partner_id
                from argil_account_move_line line
                    inner join account_journal journal on line.journal_id=journal.id --and journal.type <> 'situation'
                where --line.state='valid' and 
                line.partner_id is not null
                and line.account_id = _record4.id
                and line.period_id in (select id from period_ids) --(select id from account_period where name = _period_name)
                )                   
            and xline.period_id in (select pp2.id from period_ids2 pp2) 
                        --(select xperiodo.id from account_period xperiodo 
                        --where xperiodo.fiscalyear_id in (select id from account_fiscalyear where name = _period_fiscalyear)
                        --and xperiodo.name < _period_name
                        --)             
            group by xline.partner_id
            having (COALESCE(sum(xline.debit), 0.00) -  COALESCE(sum(xline.credit), 0.00)) <> 0.0;

        ------------
        ------------
        ------------
        
            insert into balanza_mensual
            (id, create_uid, create_date, account_id, account_code, period_id,
                order_code, account_name, account_level, account_type, account_user_type, 
                account_sign, partner_breakdown, period_name, company_name, debit, credit, 
                partner_id, from_partner_breakdown, initial_balance
                )
            
            select 
            (_record4.id * 10000 + xline.partner_id) id, x_uid::integer, _record4.create_date, _record4.id, _record4.account_code, _record4.period_id,
            _record4.order_code, _record4.account_name, _record4.account_level + 1, _record4.account_type, _record4.account_user_type, 
            _record4.account_sign, _record4.partner_breakdown, _record4.period_name, _record4.company_name, 0.0, 0.0,
            
            xline.partner_id, True,
            (COALESCE(sum(xline.debit), 0.00) -  COALESCE(sum(xline.credit), 0.00))::float
            from argil_account_move_line xline
                inner join account_journal xjournal on xline.journal_id=xjournal.id --and 
                --(CASE WHEN _period_month = 1 and not _period_flag_00 THEN xjournal.type <> 'situation' ELSE 1=1 END)
            where --xline.state='valid' and
                xline.account_id = _record4.id
            and xline.partner_id is null    
            and xline.period_id in (select pp2.id from period_ids2 pp2)
                        --(select xperiodo.id from account_period xperiodo 
                        --where xperiodo.fiscalyear_id in (select id from account_fiscalyear where name = _period_fiscalyear)
                        --and xperiodo.name < _period_name
                        --)             
            group by xline.partner_id
            having (COALESCE(sum(xline.debit), 0.00) -  COALESCE(sum(xline.credit), 0.00)) <> 0.0;


        END LOOP;

    END IF;


    FOR _record5 IN _cursor5
    LOOP
        --RAISE NOTICE 'Account: % => %', _record5.account_code,_record5.account_name;
        
        update balanza_mensual
        set 
            initial_balance=(select COALESCE(sum(bm.initial_balance), 0.00) from balanza_mensual bm where not bm.from_partner_breakdown and bm.account_id in (select f_account_child_ids(_record5.account_id) union all select f_account_child_consol_ids(_record5.account_id)) and bm.account_type not in ('view','consolidation')), -- bm.parent_id = _record5.account_id),
            debit=(select COALESCE(sum(bm.debit), 0.00) from balanza_mensual bm where not bm.from_partner_breakdown and bm.account_id in (select f_account_child_ids(_record5.account_id) union all select f_account_child_consol_ids(_record5.account_id)) and bm.account_type not in ('view','consolidation')),
            credit=(select COALESCE(sum(bm.credit), 0.00) from balanza_mensual bm where not bm.from_partner_breakdown and bm.account_id in (select f_account_child_ids(_record5.account_id) union all select f_account_child_consol_ids(_record5.account_id)) and bm.account_type not in ('view','consolidation'))
        where balanza_mensual.id=_record5.id;

        END LOOP;

    """

            sql4 = """

    
    update balanza_mensual
    set 
        initial_balance = initial_balance *  account_sign,
        balance = (debit-credit) * account_sign,
        ending_balance = (initial_balance + debit - credit) * account_sign,
        moves = not (initial_balance = 0.0 and debit = 0.0 and credit = 0.0);

    delete from account_monthly_balance_header where create_uid = x_uid;
    insert into account_monthly_balance_header 
    (id, create_uid,  create_date, write_date, write_uid, period_name, date)
    values
    (x_uid, x_uid, LOCALTIMESTAMP, LOCALTIMESTAMP, x_uid, _period_name, LOCALTIMESTAMP);        
    
    
    delete from account_monthly_balance where create_uid = x_uid;
    
    insert into account_monthly_balance
    (create_uid, create_date, write_date, write_uid, company_name, period_name, header_id,
    --fiscalyear_id, period_id, 
    account_id, account_code, account_name, account_level, account_type, account_internal_type, account_nature, account_sign,
    initial_balance, debit, credit, balance, ending_balance, moves, partner_id, partner_name, order_code, period_id)
    select 
        x_uid as create_uid, LOCALTIMESTAMP as create_date, LOCALTIMESTAMP as write_date, x_uid as write_uid, balanza_mensual.company_name, period_name, x_uid,
        account_id, account_code, account_name, account_level, account_type, account_user_type, account_nature, account_sign,
        initial_balance, debit, credit, balance, ending_balance,
        moves, partner.id, 
        case
        when acc.partner_breakdown and balanza_mensual.from_partner_breakdown then
            case when balanza_mensual.partner_id is null then ' Sin Empresa' else partner.name end
        else null
        end, order_code, period_id
    from balanza_mensual
        left join res_partner partner on partner.id=balanza_mensual.partner_id
        inner join account_account acc on acc.id=balanza_mensual.account_id;
    
    return true;

/*
select * from f_get_mx_account_monthly_balance(23601, 10, true, 1);
select company_name, order_code, account_code, account_name, account_level, * from account_monthly_balance 
where partner_id is not null order by order_code;

*/
END
$BODY$
LANGUAGE 'plpgsql';

                select * from f_get_mx_account_monthly_balance(%s, %s, %s, %s);      
                """ % (self.chart_account_id.id, self.period_id.id, 'True' if self.partner_breakdown else 'False', self._uid)
            #print "sql4: ", sql4
            sql = sql1 + sql4
            #print ("sql: \n %s" % sql)
            self._cr.execute(sql)
            #print ("-.-.-.-.-.-.-.-.-.-.-.-.-.-.-.-.-.")
            data = self._cr.fetchall()
            #print ("data: %s" % data)
            if not data[0]:
                raise UserError(_('Error trying to get Account Chart Balance, please verify your configuration and try again.'))
            
            if self.output == 'list_view': 
                values = [x.id for x in self.env['account.monthly_balance'].search([('create_uid', '=', self._uid)])]
                #print "values: ", values

                value = {
                    'domain'    : "[('id','in', ["+','.join(map(str,values))+"])]",
                    'name'      : _('Account Chart Balance'),
                    'view_type' : 'form',
                    'view_mode' : 'tree,form',
                    'res_model' : 'account.monthly_balance',
                    'view_id'   : False,
                    'type'      : 'ir.actions.act_window'
                }
                return value
            elif self.output == 'pdf':
                return self.env.ref('accounting_reports_consol.report_balanza_mensual_action').report_action(self.env['account.monthly_balance_header'].search([('create_uid', '=', self._uid)]))

        return




class AccountAccountLinesWizard(models.TransientModel):
    _inherit = "account.account_lines_wizard"

    @api.multi
    def button_get_info(self):
        
        context = self._context or {}

        data = context and context.get('active_ids', []) or []
        
        if self.account_id and self.account_id.id:
            _partner_id_line = "and line.partner_id=%s" % self.partner_id.id if self.partner_id.id else ""
            _product_id_line = "and line.product_id=%s" % self.product_id.id if self.product_id.id else ""
            _partner_id_move_line = "and move_line.partner_id=%s" % self.partner_id.id if self.partner_id.id else ""
            _product_id_move_line = "and move_line.product_id=%s" % self.product_id.id if self.product_id.id else ""

            
            sql1 = """
            
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

            drop function if exists f_account_mx_move_lines
            (x_account_id integer, x_period_id_start integer, x_period_id_stop integer);


            CREATE OR REPLACE FUNCTION f_account_mx_move_lines
            (x_account_id integer, x_period_id_start integer, x_period_id_stop integer)
            RETURNS TABLE(
            id integer,
            create_uid integer,
            create_date date,
            write_date date,
            write_uid integer,
            name varchar(256),
            ref varchar(256),
            move_id integer,
            user_id integer,
            journal_id integer,
            period_id integer,
            --fiscalyear_id integer,
            account_id integer,
            account_type_id integer,
            move_date date,
            move_name varchar(256),
            move_ref varchar(256),
            period_name  varchar(256),
            --fiscalyear_name varchar(120),
            account_code varchar(256),
            account_name varchar(256),
            account_level integer,
            account_type varchar(256),
            account_sign integer,
            journal_name varchar(256),
            initial_balance float,
            debit float, 
            credit float,
            ending_balance float,
            partner_id integer,
            product_id integer,
            qty float,
            sequence integer,
            amount_currency float,
            currency_id integer) 


            AS
            $BODY$
            DECLARE
                _cursor CURSOR FOR 
                    SELECT zx.id, zx.initial_balance, zx.debit, zx.credit, zx.ending_balance, 
                    zx.account_sign, zx.period_name, zx.move_date, zx.move_name 
                        from hesatec_mx_auxiliar_borrame""" + str(self._uid) + """ zx order by zx.period_name, zx.move_date, zx.move_name;
                _result record;
                last_balance float = 0;
                orden int = 0;
                _period_name_start varchar(20);
                _period_name_stop varchar(20);
                _period_flag_00 boolean;
                _period_month integer;
                _period_fiscalyear integer;
                _sign integer;

            BEGIN
                select account.sign into _sign from account_account account where account.id=x_account_id;

                
                select date_part('month', period.date_start) into _period_month from account_period period where period.id=x_period_id_start;

                select period.name into _period_name_start from account_period period where period.id=x_period_id_start;
                select period.name into _period_name_stop  from account_period period where period.id=x_period_id_stop;

                select ((select count(period.id) from account_period period
                        where period.id in 
                        (select period2.id from account_period period2 where period2.fiscalyear_id=
                            (select period3.fiscalyear_id from account_period period3 where period3.id=x_period_id_start))
                        and period.name ilike '00%') > 0) 
                    into _period_flag_00;

                select period.fiscalyear_id into _period_fiscalyear from account_period period where period.id=x_period_id_start;

                drop table if exists period_ids;
                create table period_ids as
                select ap.id
                from account_period ap 
                where ap.name >= _period_name_start and ap.name<=_period_name_stop
                and ap.fiscalyear_id in (select af1.id from account_fiscalyear af1 where af1.name in 
                                (select af2.name from account_fiscalyear af2 where af2.id=(select ap2.fiscalyear_id from account_period ap2 where ap2.name=_period_name_start limit 1)));


                drop table if exists period_ids2;
                create table period_ids2 as
                select ap.id
                from account_period ap 
                where date_stop = (select date_start from account_period where account_period.id=x_period_id_start)
                union all
                select ap.id
                from account_period ap 
                where date_stop < (select date_start from account_period where account_period.id=x_period_id_start)
                ;
                --and ap.fiscalyear_id in (select af1.id from account_fiscalyear af1 where af1.name in 
                --                (select af2.name from account_fiscalyear af2 where af2.id=(select ap2.fiscalyear_id from account_period ap2 where ap2.name=_period_name_start limit 1)));


                select                 
                    _sign * 
                    (
                    select COALESCE(sum(line.debit), 0.00) -  COALESCE(sum(line.credit), 0.00)
                    from account_move_line line
                        inner join account_journal journal on line.journal_id=journal.id --and 
                        --(CASE WHEN _period_month = 1 and not _period_flag_00 THEN journal.type <> 'situation' ELSE 1=1 END)
                    where --line.state='posted' and
                        line.account_id in (select f_account_child_ids(x_account_id) union all select f_account_child_consol_ids(x_account_id))
                    and line.period_id in (select period_ids2.id from period_ids2)
                                        --(select xperiodo.id from account_period xperiodo 
                                        --where xperiodo.fiscalyear_id = _period_fiscalyear
                                        --and xperiodo.name < _period_name_start
                                        --)
                    """ + _partner_id_line + """
                    """ + _product_id_line + """
                    )::float
                    --initial_balance                
                into last_balance;
                """
            
            
            
            sql2 = """
                drop table if exists hesatec_mx_auxiliar_borrame""" + str(self._uid) + """;


                create table hesatec_mx_auxiliar_borrame""" + str(self._uid) + """ AS 
                select move_line.id, move_line.name as name, move_line.ref as ref,
                move.date move_date, move.name move_name, move.ref move_ref, 
                period.name period_name, 
                --fiscalyear.name fiscalyear_name, 
                account.code account_code, account.name account_name, account.level account_level,
                account_type.name account_type, account.sign account_sign, account.id account_id, account_type.id account_type_id,
                journal.name journal_name, move.id move_id, move.create_uid user_id, journal.id journal_id, period.id period_id,
                --fiscalyear.id fiscalyear_id,
                0.00::float initial_balance,
                coalesce(move_line.debit, 0.0)::float debit,
                coalesce(move_line.credit, 0.0)::float credit,
                0.00::float ending_balance,
                move_line.partner_id,
                move_line.product_id,
                move_line.quantity::float qty,
                0::integer as sequence,
                move_line.amount_currency::float amount_currency,
                move_line.currency_id
                from account_move move--, account_period period
                    inner join account_move_line move_line on move.id = move_line.move_id
                    inner join account_account account on move_line.account_id = account.id
                    inner join account_account_type account_type on account.user_type_id = account_type.id
                    inner join account_journal journal on journal.id = move_line.journal_id --and journal.type <> 'situation' 
                    inner join account_period period on move_line.period_id=period.id and period.id in (select period_ids.id from period_ids)
                                                                                      --and period.name >= _period_name_start
                                                                                      --and period.name  <= _period_name_stop 
                where 
                move.state='posted'
                --and move_line.state='valid'
                """ + _partner_id_move_line + """
                """ + _product_id_move_line + """
                and account.id  in (select f_account_child_ids(x_account_id) union all select f_account_child_consol_ids(x_account_id))
                order by period.name, move.date, move.name;



                FOR _record IN _cursor
                LOOP
                    orden = orden + 1;
                    update hesatec_mx_auxiliar_borrame""" + str(self._uid) + """ xx
                    set sequence = orden,
                        initial_balance = last_balance, 
                        ending_balance = last_balance + 
                            (xx.account_sign * (xx.debit - xx.credit))
                    where xx.id=_record.id;

                    last_balance = last_balance + (_record.account_sign * (_record.debit - _record.credit));
                END LOOP;
    
                return query 
                    select  zz.id, 
                    zz.user_id create_uid, 
                    current_date create_date, 
                    current_date write_date, 
                     zz.user_id write_uid, 
                     zz.name, 
                     zz.ref,
                     zz.move_id, 
                     zz.user_id, 
                     zz.journal_id, 
                     zz.period_id, 
                     --zz.fiscalyear_id,
                     zz.account_id, 
                     zz.account_type_id, 
                     zz.move_date, 
                     zz.move_name, 
                     zz.move_ref, 
                        zz.period_name, 
                        --zz.fiscalyear_name, 
                        zz.account_code, 
                        zz.account_name, 
                        zz.account_level,   
                        zz.account_type, 
                        zz.account_sign, 
                        zz.journal_name, 
                        zz.initial_balance, 
                        zz.debit, 
                        zz.credit, 
                        zz.ending_balance, 
                        zz.partner_id, 
                        zz.product_id, 
                        zz.qty, 
                        zz.sequence, 
                        zz.amount_currency, 
                        zz.currency_id
                    from hesatec_mx_auxiliar_borrame""" + str(self._uid) + """ zz
                    order by sequence, period_name, move_date;


            END
            $BODY$
            LANGUAGE 'plpgsql' ;
            """
            
            
            
            sql3 = """
                delete from account_account_lines_header;-- where create_uid=""" + str(self._uid) + """;
                insert into account_account_lines_header
                (id, create_uid, create_date, write_date, write_uid, 
                account_id, period_id_start, period_id_end, partner_id, product_id)
                values
                (""" + str(self._uid) + """, """ + str(self._uid) + """, LOCALTIMESTAMP, 
                LOCALTIMESTAMP, """ + str(self._uid) + """, 
                """ + str(self.account_id.id) + """, 
                """ + str(self.period_id_start.id) + """, 
                """ + str(self.period_id_stop.id) + """,
                """ + (self.partner_id and str(self.partner_id.id) or "null")+ """,
                """ + (self.product_id and str(self.product_id.id) or "null")+ """
                );
                
                delete from account_account_lines; -- where create_uid=""" + str(self._uid) + """;

                insert into account_account_lines 
                (id, create_uid, create_date, write_date, write_uid, header_id,
                name, move_id, user_id, journal_id, period_id,
                --fiscalyear_id, 
                account_id, account_type_id, move_date, move_name, 
                move_ref, period_name, 
                --fiscalyear_name, 
                account_code, account_name, 
                account_level, account_type, account_sign, journal_name, initial_balance, debit, credit, ending_balance, 
                partner_id, product_id, qty, sequence, amount_currency, currency_id)
                select id, create_uid, create_date, write_date, write_uid, """ + str(self._uid) + """,
                name, move_id, user_id, journal_id, period_id,
                --fiscalyear_id, 
                account_id, account_type_id, move_date, move_name, 
                move_ref, period_name, 
                --fiscalyear_name, 
                account_code, account_name, 
                account_level, account_type, account_sign, journal_name, initial_balance, debit, credit, ending_balance, partner_id, product_id, qty, sequence, amount_currency, currency_id
                from f_account_mx_move_lines(%s, %s, %s);
                drop table if exists hesatec_mx_auxiliar_borrame%s;
                
                update account_account_lines_header 
                set debit_sum=(select sum(debit) from account_account_lines where header_id=%s),
                    credit_sum=(select sum(credit) from account_account_lines where header_id=%s)
                where id=%s;

                
                """ % (self.account_id.id, self.period_id_start.id, self.period_id_stop.id, self._uid, self._uid, self._uid, self._uid)
        

            sql = sql1 + sql2 + sql3
            
            self._cr.execute(sql)
            if self.output == 'list_view':
                values = [x.id for x in self.env['account.account_lines'].search([('create_uid', '=', self._uid)])]
                value = {
                    'domain': "[('id','in', ["+','.join(map(str,values))+"])]",
                    'view_type': 'form',
                    'view_mode': 'tree,form',
                    'res_model': 'account.account_lines',
                    'view_id': False,
                    'type': 'ir.actions.act_window',
                    }

                return value
            elif self.output == 'pdf':
                return self.env.ref('accounting_reports_consol.report_auxiliar_cuentas_action').report_action(self.env['account.account_lines_header'].search([('create_uid', '=', self._uid)]))
                return self.env['report'].get_action(self.env['account.account_lines_header'].search([('create_uid', '=', self._uid)]), 
                                                     'accounting_reports_consol.report_auxiliar_cuentas')

                


# # # # # # # # # # # # # # # # # # # # #
class AccountMXReportDataWizard(models.TransientModel):
    _inherit = "account.mx_report_data_wizard"

    @api.multi
    def get_info(self):

        context = dict(self._context.copy() or {})

        data = context and context.get('active_ids', []) or []

        if self.report_id and self.report_id.id:

            self._cr.execute("""
            
            ---- Agregado para desglose de Partidas usado en el reporte
            
            drop function if exists f_get_mx_report_data_entries
            (x_account_id integer, x_period_id_start integer, x_period_id_stop integer);

            CREATE OR REPLACE FUNCTION f_get_mx_report_data_entries
            (x_account_id integer, x_period_id_start integer, x_period_id_stop integer)
            RETURNS TABLE(
            id integer,
            create_uid integer,
            create_date date,
            write_date date,
            write_uid integer,
            name varchar(64),
            move_id integer,
            user_id integer,
            journal_id integer,
            period_id integer,
            fiscalyear_id integer,
            account_id integer,
            account_type_id integer,
            move_date date,
            move_name varchar(120),
            move_ref varchar(120),
            period_name  varchar(120),
            fiscalyear_name varchar(120),
            account_code varchar(60),
            account_name varchar(120),
            account_level integer,
            account_type varchar(60),
            account_sign integer,
            journal_name varchar(60),
            initial_balance float,
            debit float, 
            credit float,
            ending_balance float,
            partner_id integer,
            product_id integer,
            qty float,
            sequence integer,
            amount_currency float,
            currency_id integer) 


            AS
            $BODY$
            DECLARE
                _cursor CURSOR FOR 
                    SELECT zx.id, zx.initial_balance, zx.debit, zx.credit, zx.ending_balance, zx.account_sign, zx.period_name, zx.move_date 
                        from report_data_entries zx order by zx.period_name, zx.move_date;
                _result record;
                last_balance float = 0;
                orden int = 0;
                _fiscalyear_id integer;
            BEGIN

                select fiscal.id into _fiscalyear_id
                from account_fiscalyear fiscal where fiscal.id = (select account_period.fiscalyear_id from account_period where account_period.id = $2);


                select 
                case date_part('month', period.date_start)
                    when 1 then 
                    account_type.sign * 
                    (select COALESCE(sum(line.debit), 0.00) -  COALESCE(sum(line.credit), 0.00)
                    from account_move move, account_move_line line, account_journal journal
                    where move.id = line.move_id and move.state='posted' 
                    --and line.state='valid' 
                    and line.account_id in (select f_account_child_ids(account.id))
                    and line.journal_id = journal.id and journal.type='situation'
                    and line.period_id = period.id
                    )
                    else
                        account_type.sign * 
                        (select COALESCE(sum(line.debit), 0.00) -  COALESCE(sum(line.credit), 0.00)
                        from account_move move, account_move_line line, account_journal journal
                        where move.id = line.move_id and move.state='posted' 
                        --and line.state='valid' 
                        and line.account_id in (select f_account_child_ids(account.id))
                        and line.journal_id = journal.id --and journal.type='situation'
                        and line.period_id in 
                        (select xperiodo.id from account_period xperiodo 
                          where xperiodo.fiscalyear_id=fiscalyear.id 
                        and xperiodo.name < period.name 
                        )
                    )
                    end::float
                    --initial_balance
                
                from account_period period, account_fiscalyear fiscalyear,
                account_account account,
                account_account_type account_type
                where account.id in (select f_account_child_ids($1))
                and account.active = True
                and period.id=$2
                and account.user_type=account_type.id 
                and period.fiscalyear_id = fiscalyear.id
                into last_balance;

                drop table if exists report_data_entries;


                create table report_data_entries AS 
                select move_line.id * 1000 + period.id as id, move.name as name, move.date move_date, move.name move_name, move.ref move_ref, period.name period_name, 
                fiscalyear.name fiscalyear_name, account.code account_code, account.name account_name, account.level account_level, account_type.name account_type,  
                account_type.sign account_sign,
                account.id account_id, account_type.id account_type_id,
                journal.name journal_name,
                move.id move_id, 
                move.create_uid user_id,
                journal.id journal_id,
                period.id period_id,
                fiscalyear.id fiscalyear_id,
                0.00::float initial_balance,
                coalesce(move_line.debit, 0.0)::float debit,
                coalesce(move_line.credit, 0.0)::float credit,
                0.00::float ending_balance,
                move_line.partner_id,
                move_line.product_id,
                move_line.quantity::float qty,
                0::integer as sequence,
                move_line.amount_currency::float amount_currency,
                move_line.currency_id
                from account_move move, account_move_line move_line, account_period period, account_fiscalyear fiscalyear,
                account_account account, account_account_type account_type,  account_journal journal
                where 
                move.id = move_line.move_id and move.state='posted' and
                move_line.period_id = period.id and --move_line.state='valid' and
                fiscalyear.id = period.fiscalyear_id and
                move_line.account_id = account.id and
                account.user_type = account_type.id and
                journal.id = move_line.journal_id and journal.type <> 'situation' 
                and account.id  in (select f_account_child_ids($1))
                and period.date_start >= (select _periodo1.date_start from account_period _periodo1 where _periodo1.id=$2)
                and period.date_stop  <= (select _periodo2.date_stop from account_period _periodo2 where _periodo2.id=$3)

                order by period.name, move.date;



                FOR _record IN _cursor
                LOOP
                    orden = orden + 1;
                    update report_data_entries xx
                    set sequence = orden,
                        initial_balance = last_balance, 
                        ending_balance = last_balance + 
                            (xx.account_sign * (xx.debit - xx.credit))
                    where xx.id=_record.id;

                    last_balance = last_balance + (_record.account_sign * (_record.debit - _record.credit));
                END LOOP;
    
                return query 
                    select  zz.id, 
                    zz.user_id create_uid, 
                    current_date create_date, 
                    current_date write_date, 
                     zz.user_id write_uid, 
                     zz.name, 
                     zz.move_id, 
                     zz.user_id, 
                     zz.journal_id, 
                     zz.period_id, 
                     zz.fiscalyear_id,
                     zz.account_id, 
                     zz.account_type_id, 
                     zz.move_date, 
                     zz.move_name, 
                     zz.move_ref, 
                        zz.period_name, 
                        zz.fiscalyear_name, 
                        zz.account_code, 
                        zz.account_name, 
                        zz.account_level,   
                        zz.account_type, 
                        zz.account_sign, 
                        zz.journal_name, 
                        zz.initial_balance, 
                        zz.debit, 
                        zz.credit, 
                        zz.ending_balance, 
                        zz.partner_id, 
                        zz.product_id, 
                        zz.qty, 
                        zz.sequence, 
                        zz.amount_currency, 
                        zz.currency_id
                    from report_data_entries zz
                    order by sequence, period_name, move_date;


            END
            $BODY$
            LANGUAGE 'plpgsql' ;

            -- Ejemplo de uso:
            -- select * from f_get_mx_report_data_entries(11875, 13, 13);
            -- Donde:
            --      11875 = Cuenta contable (ID)
            --      13 => ID del Periodo Inicial
            --      13 => ID del Periodo Final
            -----------------------------------------
            
                drop function if exists f_get_mx_report_data_detail_line
                (x_report_id integer, x_period_id integer, x_uid integer, x_parent_id integer, x_parent_group varchar(64));


                CREATE OR REPLACE FUNCTION f_get_mx_report_data_detail_line
                --(x_report_definition_id integer)
                ()
                RETURNS boolean
                AS
                $BODY$

                DECLARE
                _cursor2 CURSOR FOR 
                    SELECT _z.id, _z.account_id, _z.period_id
                    from account_mx_report_data _z
                    where _z.account_entries;
                _result2 record;

                BEGIN
                    FOR _record2 IN _cursor2
                    LOOP
                        insert into account_mx_report_data_line
                            (data_id, name, move_id, user_id, journal_id, 
                            period_id, fiscalyear_id, account_id, account_type_id, move_date,
                            move_name, move_ref, period_name, fiscalyear_name, account_code,
                            account_name, account_level, account_type, account_sign, journal_name,
                            initial_balance, debit, credit, ending_balance, partner_id,
                            product_id, qty, sequence, amount_currency, currency_id)
                        select 
                            _record2.id, name, move_id, user_id, journal_id, 
                            period_id, fiscalyear_id, account_id, account_type_id, move_date,
                            move_name, move_ref, period_name, fiscalyear_name, account_code,
                            account_name, account_level, account_type, account_sign, journal_name,
                            initial_balance, debit, credit, ending_balance, partner_id,
                            product_id, qty, sequence, amount_currency, currency_id
                            from f_get_mx_report_data_entries(_record2.account_id, _record2.period_id, _record2.period_id);
                    END LOOP;

                    return true;

                END
                $BODY$
                LANGUAGE 'plpgsql';
            
            
                drop function if exists f_get_mx_report_data_detail
                (x_report_id integer, x_period_id integer, x_uid integer, x_parent_id integer, x_parent_group varchar(64));


                CREATE OR REPLACE FUNCTION f_get_mx_report_data_detail
                (x_report_id integer, x_period_id integer, x_uid integer, 
                x_parent_id integer, x_parent_group varchar(64))
                RETURNS TABLE
                (
                create_uid integer,
                create_date timestamp,
                write_date timestamp,
                write_uid integer,
                report_id integer,
                report_group varchar(64),
                report_section varchar(64),
                sequence integer,
                report_sign float,
                account_sign float,
                account_id integer,
                account_code varchar(64),
                account_name varchar(128),
                period_id integer,
                initial_balance float,
                debit float, 
                credit float, 
                account_entries boolean) 

                AS
                $BODY$

                BEGIN

                    return query 
                    select 
                        x_uid, LOCALTIMESTAMP, LOCALTIMESTAMP, x_uid,
                        subreport.parent_id,
                        case char_length(x_parent_group) 
                        when 0 then subreport.internal_group 
                        else x_parent_group
                        end,
                        subreport.name,
                        subreport.sequence,
                        case subreport.sign
                        when 'positive' then 1.0
                        else -1.0
                        end::float,
                        account_type.sign::float, 
                        account.id,
                        account.code, 
                        account.name, 
                        period.id,

                        case date_part('month', period.date_start)
                        when 1 then 
                            account_type.sign * 
                            (select COALESCE(sum(line.debit), 0.00) -  COALESCE(sum(line.credit), 0.00)
                            from account_move move, account_move_line line, account_journal journal
                            where move.id = line.move_id and move.state='posted' 
                            --and line.state='valid' 
                            and line.account_id in (select f_account_child_ids(account.id))
                            and line.journal_id = journal.id and journal.type='situation'
                            and line.period_id = period.id
                            )
                        else
                            account_type.sign * 
                            (select COALESCE(sum(line.debit), 0.00) -  COALESCE(sum(line.credit), 0.00)
                            from account_move move, account_move_line line, account_journal journal
                            where move.id = line.move_id and move.state='posted' 
                            --and line.state='valid' 
                            and line.account_id in (select f_account_child_ids(account.id))
                            and line.journal_id = journal.id 
                            and line.period_id in 
                                (select xperiodo.id from account_period xperiodo 
                                where xperiodo.fiscalyear_id= (select fiscalyear.id from account_fiscalyear fiscalyear where period.fiscalyear_id = fiscalyear.id)
                                and xperiodo.name < period.name 
                                )
                            )
                        end::float,
                        (select COALESCE(sum(line.debit), 0.00) 
                        from account_move move, account_move_line line, account_journal journal
                        where move.id = line.move_id and move.state='posted' 
                        --and line.state='valid' 
                        and line.account_id in (select f_account_child_ids(account.id))
                        and line.journal_id = journal.id and journal.type<>'situation'
                        and line.period_id = period.id)::float
                        ,
                        (select COALESCE(sum(line.credit), 0.00) 
                        from account_move move, account_move_line line, account_journal journal
                        where move.id = line.move_id and move.state='posted' 
                        --and line.state='valid' 
                        and line.account_id in (select f_account_child_ids(account.id))
                        and line.journal_id = journal.id and journal.type<>'situation'
                        and line.period_id = period.id)::float,
                        subreport.account_entries
                        
                        from account_period period, 
                        account_mx_report_definition subreport 
                            left join account_account_mx_reports_rel subreport_accounts on subreport_accounts.mx_report_definition_id = subreport.id
                            left join account_account account on subreport_accounts.account_id = account.id
                            left join account_account_type account_type on account.user_type=account_type.id    
                        where period.id=x_period_id and
                        case x_parent_id 
                        when 0 then subreport.id = x_report_id
                        else subreport.parent_id = x_parent_id
                        end
                        order by subreport.parent_id, subreport.sequence, account.code;




                END
                $BODY$
                LANGUAGE 'plpgsql';

                --select * from f_get_mx_report_data_detail(14, 24, 1, 2)

                drop function if exists f_get_mx_report_data
                (x_report_id integer, x_period_id integer, x_uid integer);


                CREATE OR REPLACE FUNCTION f_get_mx_report_data
                (x_report_id integer, x_period_id integer, x_uid integer)
                RETURNS boolean 

                AS
                $BODY$

                DECLARE
                _cursor CURSOR FOR 
                    SELECT _a.id, _a.report_id, _a.parent_id, _a.name as report_section, case _a.sign when 'positive' then 1.0::float else -1.00::float end sign,
                    _a.sequence, _a.report_id_use_resume, _a.report_id_account, _a.report_id_label, _a.report_id_show_result, _a.internal_group     
                    from account_mx_report_definition _a 
                        where _a.parent_id = x_report_id 
                        order by _a.sequence;
                _result record;

                BEGIN
                    delete from account_mx_report_data;
                    delete from account_mx_report_data_line;
                    FOR _record IN _cursor
                    LOOP
                        insert into account_mx_report_data
                        (
                            create_uid, create_date, write_date, write_uid,
                        report_id, report_group, report_section, sequence, report_sign, account_sign, 
                        account_code, account_name, account_id, account_entries,
                        period_id, 
                        initial_balance, debit, credit, ending_balance, debit_credit_ending_balance
                            )

                        select 
                        create_uid, create_date, write_date, write_uid,
                        report_id, report_group, report_section, sequence, report_sign, account_sign, 
                        account_code, account_name, account_id, account_entries,
                        period_id, 
                        initial_balance, debit, credit,
                        (initial_balance  + account_sign * (debit - credit)) ending_balance,
                        (account_sign * (debit - credit)) debit_credit_ending_balance
                        from f_get_mx_report_data_detail(_record.id, x_period_id, x_uid, 0, '');
                        
                        IF _record.report_id is not null THEN
                            --RAISE NOTICE 'Hay un subreporte para % y la casilla resumido está en %', _record.report_section, _record.report_id_use_resume;
    
                            IF not _record.report_id_use_resume THEN
                                --RAISE NOTICE 'Entramos a generar el detalle del subreporte';
                                insert into account_mx_report_data
                                (
                                create_uid, create_date, write_date, write_uid,
                                report_id, report_group, report_section, sequence, report_sign, account_sign, 
                                account_code, account_name, --account_id, 
                                period_id, 
                                initial_balance, debit, credit, ending_balance, debit_credit_ending_balance
                                )
                                select 
                                create_uid, create_date, write_date, write_uid,
                                report_id, report_group, report_section, sequence, report_sign, account_sign, 
                                account_code, account_name, --account_id, 
                                period_id, 
                                initial_balance, debit, credit,
                                (initial_balance  + account_sign * (debit - credit)) ending_balance,
                                (account_sign * (debit - credit)) debit_credit_ending_balance               
                                from f_get_mx_report_data_detail(0, x_period_id, x_uid, _record.report_id, _record.internal_group);
                            ELSE
                                --RAISE NOTICE 'Generando solo el resultado del subreporte';
                                insert into account_mx_report_data
                                (
                                create_uid, create_date, write_date, write_uid,
                                report_id, report_group, report_section, sequence, report_sign, account_sign, 
                                account_code, account_name, --account_id, 
                                period_id, 
                                initial_balance, debit, credit, ending_balance, debit_credit_ending_balance
                                )
                                select 
                                create_uid, create_date, write_date, write_uid,
                                _record.parent_id as report_id, report_group, _record.report_section report_section, _record.sequence as sequence, _record.sign as report_sign, 1 as account_sign, 
                                _record.report_id_account::varchar(64) as account_code, _record.report_id_label::varchar(64) as account_name, period_id, 
                                --sum(initial_balance) initial_balance, sum(debit) debit, sum(credit) credit,
                               sum(initial_balance * report_sign) as initial_balance, 0.0::float as debit, 0.0::float as credit,
                                sum(report_sign * (initial_balance  + account_sign * (debit - credit))) ending_balance,
                                sum(report_sign * account_sign * (debit - credit)) debit_credit_ending_balance
                                from f_get_mx_report_data_detail(0, x_period_id, x_uid, _record.report_id, _record.internal_group)
                                group by 
                                create_uid, create_date, write_date, write_uid,
                                report_id, report_group, period_id;         
                            END IF;
                        END IF;

                    END LOOP;

                    return true;

                END
                $BODY$
                LANGUAGE 'plpgsql';
                select * from f_get_mx_report_data(""" + str(self.report_id.id) + "," + str(self.period_id.id) + "," +  str(self._uid) + ")")

            data = filter(None, map(lambda x:x[0], self._cr.fetchall()))
            if not data[0]:
                raise UserError(_('Error trying to get info for this report, please verify your configuration and try again.'))

            self._cr.execute("select * from f_get_mx_report_data_detail_line();")
            values = self.env['account.mx_report_data'].search([('id', '!=', 0)])
            
            
            if values:
                report_mx = self.env['account.mx_report_data']
                initial_balance_global = 0.0
                debit_global = 0.0
                credit_global = 0.0
                ending_balance_global = 0.0
                debit_credit_ending_balance_global = 0.0
                report_group_list = []
                self._cr.execute("select report_group from account_mx_report_data;")
                report_group_cr = self._cr.fetchall()
                for rp in report_group_cr:
                    if rp[0] not in report_group_list:
                        report_group_list.append(rp[0])
                if  self.print_detail:
                    for report in report_group_list:
                        ids_to_update = report_mx.search([('report_group','=',str(report))])

                        initial_balance = 0.0
                        debit = 0.0
                        credit = 0.0
                        ending_balance = 0.0
                        debit_credit_ending_balance = 0.0

                        self._cr.execute("""select sum(initial_balance) from account_mx_report_data where id in %s""",(tuple(ids_to_update),))
                        initial_balance_cr = self._cr.fetchall()
                        if initial_balance_cr:
                            initial_balance = initial_balance_cr[0][0] if initial_balance_cr[0][0] != None else 0.0
                        self._cr.execute("""select sum(debit) from account_mx_report_data where id in %s""" ,(tuple(ids_to_update),))
                        debit_cr = self._cr.fetchall()
                        if debit_cr:
                            debit = debit_cr[0][0] if debit_cr[0][0] != None else 0.0
                        self._cr.execute("""select sum(credit) from account_mx_report_data where id in %s""" ,(tuple(ids_to_update),))
                        credit_cr = self._cr.fetchall()
                        if credit_cr:
                            credit = credit_cr[0][0] if credit_cr[0][0] != None else 0.0
                        self._cr.execute("""select sum(ending_balance) from account_mx_report_data where id in %s""" ,(tuple(ids_to_update),))
                        ending_balance_cr = self._cr.fetchall()
                        if ending_balance_cr:
                            ending_balance = ending_balance_cr[0][0] if ending_balance_cr[0][0] != None else 0.0
                        
                        self._cr.execute("""select sum(debit_credit_ending_balance) from account_mx_report_data where id in %s""" ,(tuple(ids_to_update),))
                        debit_credit_ending_balance_cr = self._cr.fetchall()
                        if debit_credit_ending_balance_cr:
                            debit_credit_ending_balance = debit_credit_ending_balance_cr[0][0] if debit_credit_ending_balance_cr[0][0] != None else 0.0
                        
                        ctx = self._context.copy()
                        ctx.update({'ids':ids_to_update,'_ids':ids_to_update})
                        report_mx.with_context(ctx).write({
                            'initial_balance_sum': initial_balance,
                            'debit_sum': debit,
                            'credit_sum': credit,
                            'ending_balance_sum': ending_balance,
                            'debit_credit_ending_balance_sum': debit_credit_ending_balance,
                            })
                        ############### GLOBALES
                    ########## ACTUALIZANDO LOS DATOS GLOBALES
                    self._cr.execute("""select sum(initial_balance*report_sign) from account_mx_report_data where id in %s""",(tuple(values),))
                    initial_balance_global_cr = self._cr.fetchall()
                    if initial_balance_global_cr:
                        initial_balance_global = initial_balance_global_cr[0][0] if initial_balance_global_cr[0][0] != None else 0.0
                    self._cr.execute("""select sum(debit*report_sign) from account_mx_report_data where id in %s""" ,(tuple(values),))
                    debit_global_cr = self._cr.fetchall()
                    if debit_global_cr:
                        debit_global = debit_global_cr[0][0] if debit_global_cr[0][0] != None else 0.0
                    self._cr.execute("""select sum(credit*report_sign) from account_mx_report_data where id in %s""" ,(tuple(values),))
                    credit_global_cr = self._cr.fetchall()
                    if credit_global_cr:
                        credit_global = credit_global_cr[0][0] if credit_global_cr[0][0] != None else 0.0
                    self._cr.execute("""select sum(ending_balance*report_sign) from account_mx_report_data where id in %s""" ,(tuple(values),))
                    ending_balance_global_cr = self._cr.fetchall()
                    if ending_balance_global_cr:
                        ending_balance_global = ending_balance_global_cr[0][0] if ending_balance_global_cr[0][0] != None else 0.0
                    
                    self._cr.execute("""select sum(debit_credit_ending_balance*report_sign) from account_mx_report_data where id in %s""" ,(tuple(values),))
                    debit_credit_ending_balance_global_cr = self._cr.fetchall()
                    if debit_credit_ending_balance_global_cr:
                        debit_credit_ending_balance_global = debit_credit_ending_balance_global_cr[0][0] if debit_credit_ending_balance_global_cr[0][0] != None else 0.0
                    ctx.update({'ids':values,'_ids':values})
                    report_mx.with_context(ctx).write({
                        'initial_balance_global': initial_balance_global,
                        'debit_global': debit_global,
                        'credit_global': credit_global,
                        'ending_balance_global': ending_balance_global,
                        'debit_credit_ending_balance_global': debit_credit_ending_balance_global,
                        })                    

                    value = {
                        'type'          : 'ir.actions.report.xml',
                        'report_name'   : 'ht_reportes_contables_pdf' if self.report_type == 'pdf' else 'ht_reportes_contables_xls',
        
                        'datas'         : {
                                            'model' : 'account.mx_report_data',
                                            'ids'   : values,
        
                                            }
                            }
                else:
                    value = {
                            'type'          : 'ir.actions.report.xml',
                            'report_name'   : 'ht_reportes_contables_pdf_not_detail' if self.report_type == 'pdf' else 'ht_reportes_contables_xls_not_detail',
                            
                            'datas'         : {
                                                'model' : 'account.mx_report_data',
                                                'ids'   : values,
            
                                                }
                                } 

        return value






