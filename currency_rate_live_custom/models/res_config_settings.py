# -*- coding: utf-8 -*-

import datetime
from lxml import etree, objectify
from dateutil.relativedelta import relativedelta
import re
import logging
from pytz import timezone
import requests
import suds.client
import json
import time as ti
from odoo import api, fields, models
from odoo.addons.web.controllers.main import xml2json_from_elementtree
from odoo.exceptions import UserError
from odoo.tools.translate import _
from odoo.tools import DEFAULT_SERVER_DATE_FORMAT

BANXICO_DATE_FORMAT = '%Y-%m-%d'

logger = logging.getLogger(__name__)

def get_url(url):
    try:
        page = requests.get(url)
        content = page.text
        return content
    except ImportError:
        raise Exception('Error: Unable to import urllib !')
    except IOError:
        raise Exception('Error: Web Service [%s] does not exist or it is non accesible !' % url)

class ResCompany(models.Model):
    _inherit = 'res.company'

    currency_provider = fields.Selection(selection_add=[('dof', 'DOF')])

    def _update_currency_dof(self):
        #def update_rate(currency, rate, date):
        def update_rate(currency, rate, date, rate_custom):
            #  Deleting current rate values because we can only have one
            currency.rate_ids.filtered(lambda r: date == r.name).unlink()
            currency.rate_ids.create({
                'rate': rate,
                'currency_id': currency.id,
                'name': date,
                'rate_custom': rate_custom,
            })
            # Update cached rate field
            logger.error('currency: %s', currency)
            currency._compute_current_rate()

        date_today = fields.Date.today()
        date_today = date_today.strftime('%d-%m-%Y')    
        #logger.error('date_today: %s', date_today)   
        url = "https://sidofqa.segob.gob.mx/dof/sidof/indicadores/158/"
        respuesta =  requests.get(url+str(date_today)+"/"+str(date_today))  
        datos = json.loads(respuesta.text) 
        logger.error('datos: %s', datos) 
        usd_mxn = 0
        if datos["messageCode"] != 200:
            raise Exception("No fue posible consultar los Indicadores " + datos["response"])
            #return 0

        if datos["TotalIndicadores"]:
            if datos["TotalIndicadores"] == 1:
                for indice in datos["ListaIndicadores"]:
                    usd_mxn = indice["valor"]
            else:
                raise Exception("La lista contiene " + str(datos["TotalIndicadores"]) + " Indicadores" )
        else:
            raise Exception("No fue posible consultar los Indicadores" )
        #url = 'http://dof.gob.mx/indicadores_detalle.php?cod_tipo_indicador=158&hfecha='+date_today[-2:]+'%2F'+date_today[5:7]+'%2F'+date_today[:4]+'&hfecha='+date_today[-2:]+'%2F'+date_today[5:7]+'%2F'+date_today[:4]'&accionI=imprimir'
        #http://dof.gob.mx/indicadores_detalle.php?cod_tipo_indicador=158&
        #url = 'http://dof.gob.mx/indicadores_detalle.php?cod_tipo_indicador=158&hfecha='+date_today+'&dfecha='+date_today+'&accionI=imprimir'
        #logger.error('url: %s', url)
        #data = get_url(url)
        
        """if data:
            logger.info("%s", "DOF sent a response")
        else:
            raise Exception('Error retrieving info from DOF. No data retrieved from http://dof.gob.mx')"""

        #res_id = re.findall('<title>DOF - Diario Oficial de la Federaci&oacute;n</title>', data.text)
        
        """if not (res_id and len(res_id) > 0):
            logger.info('Error retrieving info from DOF. Page data could not be recognized!')
            return True"""
        #res_id = re.findall('''<td width="52%" align="center" class="txt">(\d+.\d+)</td>''', data)
        #logger.error('res_id: %s', res_id)
        """if not (res_id and len(res_id) > 0):
            logger.info("Error retrieving info from DOF. Exchange rates not found!")
            return True"""
        #usd_mxn = float(res_id[0])

       
        mxn = self.env.ref('base.MXN')
        usd = self.env.ref('base.USD')
        base_currency = mxn
        date = fields.Date.today()
        currency_to_update = usd
        rate = 1.0 / float(usd_mxn)
        rate_custom = float(usd_mxn)
        
        if mxn.rate != 1 and usd.rate == 1:
            # Most of the time Mexico use USD.rate=1 and company.currency=MXN
            base_currency = usd
            currency_to_update = mxn
            rate = usd_mxn
            rate_custom = 1.0 / usd_mxn
            _logger.error('rate_custom1: %s', rate_custom)
        else:
            logger.info('tasaconvertida')
            # Force MXN.rate=1 to get a valid base
            update_rate(mxn, 1, date, 1)
        logger.error('rate_custom2: %s', rate_custom)
        update_rate(currency_to_update, rate, date, rate_custom)
        return True

   

    def update_currency_rates(self):
        logger.info('funcion moneda')
        
       
        if self.currency_provider == 'dof':
            logger.info('funcion moneda1')
            res = True
            all_good = True
            for company in self:
                logger.info('funcion moneda2')
                if company.currency_provider == 'dof':
                    res = company._update_currency_dof()
                if not res:
                    all_good = False
                    _logger.warning(_('Unable to connect to the online exchange rate platform %s. The web service may be temporary down.') % company.currency_provider)
                elif company.currency_provider:
                    company.last_currency_sync_date = fields.Date.today()
            return all_good
        else:

            rslt = True
            active_currencies = self.env['res.currency'].search([])
            for (currency_provider, companies) in self._group_by_provider().items():
                parse_results = None

                parse_function = getattr(companies, '_parse_' + currency_provider + '_data')
                parse_results = parse_function(active_currencies)

                if parse_results == False:
                    # We check == False, and don't use bool conversion, as an empty
                    # dict can be returned, if none of the available currencies is supported by the provider
                    _logger.warning(_('Unable to connect to the online exchange rate platform %s. The web service may be temporary down.') % currency_provider)
                    rslt = False
                else:
                    companies._generate_currency_rates(parse_results)

            return rslt

   