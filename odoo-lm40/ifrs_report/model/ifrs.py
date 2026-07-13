# -*- coding: utf-8 -*-

from odoo import models, fields, api
from odoo.tools.translate import _
import logging
_logger = logging.getLogger(__name__)

class IfrsIfrs(models.Model):
    _name = 'ifrs.ifrs'
    

    @api.model
    def _default_fiscalyear(self):
        af_obj = self.env['account.fiscal']
        return af_obj.find(exception=False)

    @api.onchange('company_id')
    def onchange_company_id(self):
        af_obj = self.env['account.fiscal']
        self.fiscalyear_id = af_obj.find(exception=False)
        self.currency_id = self.company_id.currency_id.id

    name = fields.Char(string='Nombre', size=128, required=True, help='Nombre Reporte')
    company_id = fields.Many2one('res.company', string='Compañía', change_default=False,
                                 required=False, readonly=True, states={},
                                 default=lambda self: self.env['res.company']._company_default_get('ifrs.ifrs'), 
                                 help='Nombre de la Compañía')
    currency_id = fields.Many2one('res.currency', string='Moneda',
                                    required=False, readonly=True, states={},
                                    related='company_id.currency_id',
                                    help=('Moneda en la que el reporte es expresado. Si no '
                                          'selecciona entonces será usada la Monedad de la Compañía'))
    
    title = fields.Char(string='Título', size=128, required=True, translate=True,
                        help='Report title that will be printed')
    code = fields.Char(string='Código', size=128, required=True,help='Report code')
    description = fields.Text(string='Descripción')
    ifrs_lines_ids = fields.One2many('ifrs.lines', 'ifrs_id', string='Líneas IFRS', readonly=False, 
                                     states={'draft': [('readonly', False)]}, copy=True)
    state = fields.Selection([('draft', 'Borrador'),
                              ('ready', 'Listo'),
                              ('done', 'Hecho'),
                              ('cancel', 'Cancelado')],
                            string='Estado', required=True, default='draft')
    fiscalyear_id = fields.Many2one('account.fiscal', string='Año Fiscal',default=_default_fiscalyear,
                                    help=('Año Fiscal a usar en el Reporte'))
    help = fields.Boolean(string='Mostrar Ayuda', default=True, copy=False,
                            help='Permite que se muestre la ayuda en el formulario')
    ifrs_ids = fields.Many2many('ifrs.ifrs', 'ifrs_m2m_rel', 'parent_id', 'child_id',
                                string='Otros Reportes', copy=True)

    @api.model
    def _get_ordered_lines(self):
        """ Return list of browse ifrs_lines per level in order ASC, for can
        calculate in order of priorities.

        Retorna la lista de ifrs.lines del ifrs_id organizados desde el nivel
        mas bajo hasta el mas alto. Lo niveles mas bajos se deben calcular
        primero, por eso se posicionan en primer lugar de la lista.
        """
        self.ensure_one()
        context = self._context.copy()
        il_obj = self.env['ifrs.lines']
        tree = {1: {}}
        for lll in self.ifrs_lines_ids:
            il_obj._get_level(lll, tree, 1)
            
        
        levels = sorted(tree)
        levels.reverse()
        ids_x = []  # List of ids per level in order ASC
        for i in levels:
            ids_x += tree[i].keys()
        return ids_x

    @api.model
    def compute(self):
        """ Se encarga de calcular los montos para visualizarlos desde
        el formulario del ifrs, hace una llamada al get_report_data, el
        cual se encarga de realizar los calculos.
        """
        context = self._context.copy()
        fy = self.env['account.fiscal'].find(exception=False)
        context.update({'whole_fy': True, 'fiscalyear': fy})
        for record in self.with_context(context).get_report_data(None, target_move='posted', two=True):
            if record['type'] == 'abstract':
                continue
            self.env['ifrs.lines'].browse(record['id']).write({'amount': record['amount']})
        return True

    @api.model
    def _get_periods_name_list(self, fiscalyear_id):
        """ Devuelve una lista con la info de los periodos fiscales
        (numero mes, id periodo, nombre periodo)
        @param fiscalyear_id: Año fiscal escogido desde el wizard encargada
        de preparar el reporte para imprimir
        """
        af_obj = self.env['account.fiscal']
        periods = self.env['account.period']

        period_list = [('0', None, ' ')]

        fiscalyear_bwr = af_obj.browse(fiscalyear_id) #af_obj.with_context(context).browse(fiscalyear_id)
        periods_ids = fiscalyear_bwr._get_fy_period_ids()

        for ii, period_id in enumerate(periods_ids, start=1):
            period_list.append((str(ii), period_id, periods.browse(period_id).name))
        return period_list
    

    @api.model
    def get_period_print_info(self, period_id, report_type):
        """ Return all the printable information about period
        @param period_id: Dependiendo del report_type, en el caso que sea
        'per', este campo indica el periodo a tomar en cuenta, en caso de que
        el report_type sea 'all', es Falso.
        @param report_type: Su valor se establece desde el wizard que se
        encarga de preparar al reporte para imprimir, el report_type puede ser
        'all' (incluir todo el año fiscal en el reporte) o 'per' (tomar en
        cuenta solo un periodo determinado en el reporte)
        """
        if report_type == 'all':
            res = _('TODOS LOS PERIODOS DEL AÑO FISCAL')
        else:
            period = self.env['account.period'].browse(period_id)
            res = '{name} [{code}]'.format(name=period.name, code=period.code)
        return res

    def step_sibling(self, new_id):
        '''
        Sometimes total_ids and operand_ids include lines from their own
        ifrs_id report, They are siblings. In this case m2m copy_data just make
        a link from the old report.
        In the new report we have to substitute the cousins that are pretending
        to be siblings with the siblings
        This can be achieved due to the fact that each line has unique sequence
        within each report, using the analogy about relatives then each
        pretending cousin is of same age than that of the actual sibling
        cousins with common parent are siblings among them
        '''
        

        old_brw = self
        new_brw = new_id 
        il_obj = self.env['ifrs.lines']

        sibling_ids = {}
        markt = []
        marko = []
        for lll in old_brw.ifrs_lines_ids:
            for ttt in lll.total_ids:
                if ttt.ifrs_id.id == lll.ifrs_id.id:
                    sibling_ids[ttt.sequence] = ttt.id
                    markt.append(lll.sequence)
            for o in lll.operand_ids:
                if o.ifrs_id.id == lll.ifrs_id.id:
                    sibling_ids[o.sequence] = o.id
                    marko.append(lll.sequence)

        if not sibling_ids:
            return True

        markt = markt and set(markt) or []
        marko = marko and set(marko) or []

        o2n = {}
        for seq in sibling_ids:
            ns_id = il_obj.search([('sequence', '=', seq),('ifrs_id', '=', new_id)])
            o2n[sibling_ids[seq]] = ns_id and ns_id[0].id

        for nl in new_brw.ifrs_lines_ids:
            if nl.sequence in markt:
                tt = [o2n.get(nt.id, nt.id) for nt in nl.total_ids]
                nl.write({'total_ids': [(6, 0, tt)]})
            if nl.sequence in marko:
                oo = [o2n.get(no.id, no.id) for no in nl.operand_ids]
                nl.write({'operand_ids': [(6, 0, oo)]})

        return True

    

    @api.model
    def get_report_data(self, wizard_id, fiscalyear=None, exchange_date=None,
                              currency_wizard=None, target_move=None, period=None, two=None):
        """ Metodo que se encarga de retornar un diccionario con los montos
        totales por periodo de cada linea, o la sumatoria de todos montos
        por periodo de cada linea. La información del diccionario se utilizara
        para llenar el reporte, ya sea de dos columnas o de 12 columnas.
        @param fiscalyear: Año fiscal que se reflejara en el reporte
        @param exchange_date:
        @param currency_wizard: Moneda que se reflejara en el reporte
        @param target_move: Asientos contables a tomar en cuenta en los
        calculos
        @param period: Periodo a reflejar en caso de que no se tome en cuenta
        todo el año fiscal
        @param two: Nos dice si el reporte es de 2 o 12 columnas
        """
        self.ensure_one()
        ctx = self._context.copy()
        data = []
        ifrs_line = self.env['ifrs.lines']
        period_name = self._get_periods_name_list(fiscalyear)
        ordered_lines = self._get_ordered_lines()
        bag = {}.fromkeys(ordered_lines, None)

        # TODO: THIS Conditional shall reduced
        one_per = period is not None

        for il_id in ordered_lines:
            ifrs_l = ifrs_line.browse(il_id)
            bag[ifrs_l.id] = {}

            line = {
                'sequence'  : int(ifrs_l.sequence),
                'id'        : ifrs_l.id,
                'name'      : ifrs_l.name,
                'invisible' : ifrs_l.invisible,
                'type'      : str(ifrs_l.type),
                'comparison': ifrs_l.comparison,
                'operator'  : ifrs_l.operator}

            if two:
                line['amount'] = ifrs_l.with_context(ctx)._get_amount_with_operands(
                    ifrs_l, period_name, fiscalyear,
                    exchange_date, currency_wizard, period, target_move,
                    two=two, one_per=one_per, bag=bag)
            else:
                line['period'] = ifrs_l.with_context(ctx)._get_dict_amount_with_operands(
                    ifrs_l, period_name, fiscalyear,
                    exchange_date, currency_wizard, None, target_move, bag=bag)

            # NOTE:Only lines from current Ifrs report record are taken into
            # account given there are lines included from other reports to
            # compute values
            if ifrs_l.ifrs_id.id == self.id:
                data.append(line)
        data.sort(key=lambda x: int(x['sequence']))
        return data
