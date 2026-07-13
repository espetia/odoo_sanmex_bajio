# -*- coding: utf-8 -*-
###########################################################################

from odoo import models, fields, api, _, release
from odoo.exceptions import UserError
from odoo.tools import float_compare, float_round, pycompat

class StockMove(models.Model):
    _inherit = "stock.move"

    def _run_valuation(self, quantity=None):
        res = super(StockMove, self)._run_valuation()
        if self.product_id.valuation == 'real_time' and not (self._is_in() or self._is_out()):
            if self.product_id.cost_method == 'fifo':
                self.env['stock.move']._run_fifo(self, quantity=quantity)
            elif self.product_id.cost_method in ['standard', 'average']:
                curr_rounding = self.company_id.currency_id.rounding
                value = -float_round(self.product_id.standard_price * (self.product_qty if quantity is None else quantity), precision_rounding=curr_rounding)
                self.write({
                    'value': value if quantity is None else self.value + value,
                    'price_unit': value / self.product_qty,
                }) 
        return res        
        if self._is_in():
            if self.product_id.cost_method in ['fifo', 'average']:
                price_unit = self._get_price_unit()
                value = price_unit * (quantity or self.product_qty)
                vals = {
                    'price_unit': price_unit,
                    'value': value if quantity is None or not self.value else self.value,
                    'remaining_value': value if quantity is None else self.remaining_value + value,
                }
                if self.product_id.cost_method == 'fifo':
                    vals['remaining_qty'] = self.product_qty if quantity is None else self.remaining_qty + quantity
                self.write(vals)
            else:  # standard
                value = self.product_id.standard_price * (quantity or self.product_qty)
                self.write({
                    'price_unit': self.product_id.standard_price,
                    'value': value if quantity is None or not self.value else self.value,
                })
        elif self._is_out():
            if self.product_id.cost_method == 'fifo':
                self.env['stock.move']._run_fifo(self, quantity=quantity)
            elif self.product_id.cost_method in ['standard', 'average']:
                curr_rounding = self.company_id.currency_id.rounding
                value = -float_round(self.product_id.standard_price * (self.product_qty if quantity is None else quantity), precision_rounding=curr_rounding)
                self.write({
                    'value': value if quantity is None else self.value + value,
                    'price_unit': value / self.product_qty,
                })    
    
    
    
    """def _action_done(self):
        #self.product_price_update_before_done()
        res = super(StockMove, self)._action_done()
        for move in res.filtered(lambda m: m.product_id.valuation == 'real_time' and not (m._is_in() or m._is_out())):
            move._account_entry_move()
        return res"""
    
    
    def _account_entry_move(self, qty, description, svl_id, cost):
        """ Accounting Valuation Entries """
        self.ensure_one()
        if self.product_id.type != 'product' or self.product_id.categ_id.property_valuation != 'real_time':
            # no stock valuation for consumable products
            return False
        if self.restrict_partner_id:
            # if the move isn't owned by the company, we don't make any valuation
            return False

        location_from = self.location_id
        location_to = self.location_dest_id
        company_from = location_from.usage == 'internal' and location_from.company_id or False
        company_to = location_to and (location_to.usage == 'internal') and location_to.company_id or False

        ###############################################
       
        ###############################################

        # (Origen: Transito  => Destino: Transito) >>>> No se genera poliza
        if location_from.usage=='transit' and location_to.usage=='transit':
            return False

        
        if location_from.usage in ('supplier','customer') \
              and location_to.usage in ('supplier','customer'):
            force_company = (company_to and company_to.id) or (company_from and company_from.id) or self.env.user.company_id.id
            journal_id, acc_src, acc_dest, acc_valuation = self._get_accounting_data_for_valuation()
            self.with_context(force_company=force_company)._create_account_move_line(acc_src, acc_dest, journal_id, qty, description, svl_id, cost)
            return

        
        if location_from.usage in ('supplier') \
              and location_to.usage in ('inventory','production'):
            force_company = (company_to and company_to.id) or (company_from and company_from.id) or self.env.user.company_id.id
            journal_id, acc_src, acc_dest, acc_valuation = self._get_accounting_data_for_valuation()
            self.with_context(force_company=force_company)._create_account_move_line(acc_src, acc_dest, journal_id, qty, description, svl_id, cost)
            return


        if location_from.usage in ('internal','transit','inventory','production') \
              and location_to.usage in ('internal','transit','inventory','production'):
            force_company = (company_to and company_to.id) or (company_from and company_from.id) or self.env.user.company_id.id
            journal_id, acc_src, acc_dest, acc_valuation = self._get_accounting_data_for_valuation()
            self.with_context(force_company=force_company)._prepare_account_move_vals(acc_src, acc_dest, journal_id, qty, description, svl_id, cost)
            return

        ###############################################
        
        ###############################################
        
        
        # Create Journal Entry for products arriving in the company; in case of routes making the link between several
        # warehouse of the same company, the transit location belongs to this company, so we don't need to create accounting entries
        if company_to and (self.location_id.usage not in ('internal', 'transit') and self.location_dest_id.usage == 'internal' or company_from != company_to):
            journal_id, acc_src, acc_dest, acc_valuation = self._get_accounting_data_for_valuation()
            if location_from and location_from.usage == 'customer':  # goods returned from customer
                self.with_context(force_company=company_to.id)._prepare_account_move_vals(acc_dest, acc_valuation, journal_id, qty, description, svl_id, cost)
            else:
                self.with_context(force_company=company_to.id)._prepare_account_move_vals(acc_src, acc_valuation, journal_id, qty, description, svl_id, cost)

        # Create Journal Entry for products leaving the company
        if company_from and (self.location_id.usage == 'internal' and self.location_dest_id.usage not in ('internal', 'transit') or company_from != company_to):
            journal_id, acc_src, acc_dest, acc_valuation = self._get_accounting_data_for_valuation()
            if location_to and location_to.usage == 'supplier':  # goods returned to supplier
                self.with_context(force_company=company_from.id)._create_account_move_line(acc_valuation, acc_src, journal_id, qty, description, svl_id, cost)
            else:
                self.with_context(force_company=company_from.id)._create_account_move_line(acc_valuation, acc_dest, journal_id, qty, description, svl_id, cost)

        if self.company_id.anglo_saxon_accounting and self.location_id.usage == 'supplier' and self.location_dest_id.usage == 'customer':
            # Creates an account entry from stock_input to stock_output on a dropship move. https://github.com/odoo/odoo/issues/12687
            journal_id, acc_src, acc_dest, acc_valuation = self._get_accounting_data_for_valuation()
            self.with_context(force_company=self.company_id.id)._create_account_move_line(acc_src, acc_dest, journal_id, qty, description, svl_id, cost)       

    
    
    @api.model
    def _get_accounting_data_for_valuation(self):
        """ Return the accounts and journal to use to post Journal Entries for
        the real-time valuation of the quant. """
        self.ensure_one()
        accounts_data = self.product_id.product_tmpl_id.get_product_accounts()
        #_logger.error('accounts_data: %s', accounts_data)
        #########################################
        
        #########################################
        journal_id = accounts_data['stock_journal'].id
        acc_src = acc_dest = acc_valuation = False
        # Transferencias entre ubicaciones de empresas 'supplier','customer'
        if self.location_id.usage in ('supplier','customer') and self.location_dest_id.usage in ('supplier','customer'):
            acc_src = (self.location_id.usage == 'supplier' and self.location_dest_id.usage == 'customer' and \
                            accounts_data['stock_input'].id) or \
                      (self.location_id.usage == 'customer' and self.location_dest_id.usage == 'supplier' and \
                            accounts_data['stock_output'].id)
            acc_dest = (self.location_id.usage == 'supplier' and self.location_dest_id.usage == 'customer' and \
                            accounts_data['stock_output'].id) or \
                       (self.location_id.usage == 'customer' and self.location_dest_id.usage == 'supplier' and \
                            accounts_data['stock_input'].id)
            acc_valuation = False
            return journal_id, acc_src, acc_dest, acc_valuation

        # Transferencias entre ubicaciones 'internal','transit','inventory','production'
        if self.location_id.usage in ('transit','production') and \
           self.location_dest_id.usage in ('transit','production'):
            acc_src = self.location_id.valuation_out_account_id and self.location_id.valuation_out_account_id.id \
                        or accounts_data.get('stock_valuation', False).id
            acc_dest = self.location_dest_id.valuation_in_account_id and self.location_dest_id.valuation_in_account_id.id \
                        or accounts_data.get('stock_valuation', False).id
            #_logger.error('acc_dest_1: %s', acc_dest)
            #_logger.error('acc_src_1: %s', acc_src)
            acc_valuation = False
            return journal_id, acc_src, acc_dest, acc_valuation
        #else:

        if self.location_id.usage in ('inventory') and self.location_dest_id.usage in ('inventory'):
            
            acc_src = self.location_id.valuation_out_account_id and self.location_id.valuation_out_account_id.id \
                    or accounts_data.get('stock_valuation', False).id
            acc_dest = self.location_id.account_cost_inventory and self.location_id.account_cost_inventory.id or self.location_dest_id.account_cost_inventory.id \
                    or accounts_data.get('stock_valuation', False).id
            _logger.error('acc_dest_1: %s', acc_dest)
            _logger.error('acc_src_1: %s', acc_src)
            
            acc_valuation = False

            return journal_id, acc_src, acc_dest, acc_valuation
        if self.location_id.usage in ('internal') and self.location_dest_id.usage in ('internal'):
            acc_src = self.location_id.valuation_out_account_id and self.location_id.valuation_out_account_id.id \
                    or accounts_data.get('stock_valuation', False).id

            acc_dest = self.location_dest_id.valuation_in_account_id and self.location_dest_id.valuation_in_account_id.id \
                    or accounts_data.get('stock_valuation', False).id       
        

            _logger.error('acc_dest_p: %s', acc_dest)
            _logger.error('acc_src_p: %s', acc_src)
            _logger.error('acc_valuation: %s', acc_valuation)
            acc_valuation = False
            return journal_id, acc_src, acc_dest, acc_valuation


        # Transferencia de Entrada por Compra y/o Devolucion de Venta
        if self.location_id.usage in ('customer','supplier') and self.location_dest_id.usage in ('internal'):
            acc_src = self.location_id.usage in ('supplier') and accounts_data['stock_input'].id or False
            acc_dest = self.location_id.usage in ('customer') and accounts_data['stock_output'].id or False
            acc_valuation = self.location_dest_id.valuation_in_account_id and self.location_dest_id.valuation_in_account_id.id \
                        or accounts_data.get('stock_valuation', False).id
            #acc_dest = acc_valuation
            return journal_id, acc_src, acc_dest, acc_valuation            


        # Transferencia de Salida Venta y/o Devolucion de Compra
        if self.location_dest_id.usage in ('customer','supplier') and self.location_id.usage in ('internal'):
            acc_src = self.location_dest_id.usage in ('supplier') and accounts_data['stock_input'].id or False
            acc_dest = self.location_dest_id.usage in ('customer') and accounts_data['stock_output'].id or self.location_id.accout_local_cost.id
            _logger.error('acc_dest_pruebas: %s', acc_dest)
            acc_valuation = self.location_id.valuation_in_account_id and self.location_id.valuation_in_account_id.id \
                        or accounts_data.get('stock_valuation', False).id
            #acc_dest = acc_valuation
            if self.location_id.accout_local_cost:
                acc_dest = self.location_id.accout_local_cost.id
            else:
                acc_dest = accounts_data['stock_output'].id
            _logger.error('acc_dest_final: %s', acc_dest)
            
            return journal_id, acc_src, acc_dest, acc_valuation

        #########################################
        
        #########################################            


        if self.location_id.valuation_out_account_id:
            acc_src = self.location_id.valuation_out_account_id.id
        else:
            acc_src = accounts_data['stock_input'].id

        if self.location_dest_id.valuation_in_account_id:
            acc_dest = self.location_dest_id.valuation_in_account_id.id
        else:
            acc_dest = accounts_data['stock_output'].id

        

        

        acc_valuation = accounts_data.get('stock_valuation', False)
        if acc_valuation:
            acc_valuation = acc_valuation.id
        if not accounts_data.get('stock_journal', False):
            raise UserError(_('You don\'t have any stock journal defined on your product category, check if you have installed a chart of accounts'))
        if not acc_src:
            raise UserError(_('Cannot find a stock input account for the product %s. You must define one on the product category, or on the location, before processing this operation.') % (self.product_id.name))
        if not acc_dest:
            raise UserError(_('Cannot find a stock output account for the product %s. You must define one on the product category, or on the location, before processing this operation.') % (self.product_id.name))
        if not acc_valuation:
            raise UserError(_('You don\'t have any stock valuation account defined on your product category. You must define one before processing this operation.'))
        journal_id = accounts_data['stock_journal'].id
        return journal_id, acc_src, acc_dest, acc_valuation