odoo.define('stock.lot.dashboard', function (require) {
    "use strict";
    /**
     * This file defines the Purchase Dashboard view (alongside its renderer, model
     * and controller). This Dashboard is added to the top of list and kanban Purchase
     * views, it extends both views with essentially the same code except for
     * _onDashboardActionClicked function so we can apply filters without changing our
     * current view.
     */

    var core = require('web.core');
    var ListController = require('web.ListController');
    var ListModel = require('web.ListModel');
    var ListRenderer = require('web.ListRenderer');
    var ListView = require('web.ListView');
    var KanbanController = require('web.KanbanController');
    var KanbanModel = require('web.KanbanModel');
    var KanbanRenderer = require('web.KanbanRenderer');
    var KanbanView = require('web.KanbanView');
    var SampleServer = require('web.SampleServer');
    var view_registry = require('web.view_registry');
    const session = require('web.session');

    var QWeb = core.qweb;

    // Add mock of method 'retrieve_dashboard' in SampleServer, so that we can have
    // the sample data in empty purchase kanban and list view
    let dashboardValues;
    SampleServer.mockRegistry.add('stock.production.lot/retrieve_stock_lot_dashboard', () => {
        return Object.assign({}, dashboardValues);
    });

    //--------------------------------------------------------------------------
    // Kanban View
    //--------------------------------------------------------------------------

    var StockLotKanbanDashboardRenderer = KanbanRenderer.extend({
        events:_.extend({}, KanbanRenderer.prototype.events, {
            'click .o_dashboard_action': '_onDashboardActionClicked',
            'click .o_button_test': '_onChangeTypeProduct',
        }),
        /**
         * @override
         * @private
         * @returns {Promise}
         */
        _render: function () {
            var self = this;
            return this._super.apply(this, arguments).then(function () {
                var values = self.state.dashboardValues;
                var stock_lot_dashboard = QWeb.render('base_logistics_sanmex.StockLotDashboard', {
                    values: values,
                });
                //self.$el.parent().find(".o_logistics_dashboard").remove();
                //self.$el.before(rentlog_dashboard);
                //$(".o_logistics_dashboard").append(stock_lot_dashboard);
                //self.$el.prepend(stock_lot_dashboard);
                self.$el.parent().find(".o_rent_logistics_dashboard").remove();
                self.$el.before(stock_lot_dashboard);
            });
        },
    
        /**
         * @private
         * @param {MouseEvent}
         */
        _onDashboardActionClicked: function (e) {
            console.log("test");
            e.preventDefault();
            var $action = $(e.currentTarget);
            this.trigger_up('dashboard_open_action', {
                action_name: "base_logistics_sanmex.stock_lot_action_dashboard_kanban",
                action_context: $action.attr('context'),
            });
        },

        _onChangeTypeProduct: function (e){
            //this.state.type_product = e.target.value;
            console.log("test");
        } 
    });

    var StockLotKanbanDashboardModel = KanbanModel.extend({
        /**
         * @override
         */
        init: function () {
            this.dashboardValues = {};
            this.type_product ="";
            this._super.apply(this, arguments);
        },
    
        /**
         * @override
         */
        __get: function (localID) {
            var result = this._super.apply(this, arguments);
            if (_.isObject(result)) {
                result.dashboardValues = this.dashboardValues[localID];
            }
            return result;
        },
        /**
         * @override
         * @returns {Promise}
         */
        __load: function () {
            return this._loadDashboard(this._super.apply(this, arguments));
        },
        /**
         * @override
         * @returns {Promise}
         */
        __reload: function () {
            return this._loadDashboard(this._super.apply(this, arguments));
        },
    
        /**
         * @private
         * @param {Promise} super_def a promise that resolves with a dataPoint id
         * @returns {Promise -> string} resolves to the dataPoint id
         */
        _loadDashboard: function (super_def) {
            var self = this;
            var dashboard_def = this._rpc({
                model: 'stock.production.lot',
                method: 'retrieve_stock_lot_dashboard',
                context: session.user_context,
            });
            return Promise.all([super_def, dashboard_def]).then(function(results) {
                var id = results[0];
                dashboardValues = results[1];
                self.dashboardValues[id] = dashboardValues;
                return id;
            });
        },
    });

    var StockLotKanbanDashboardController = KanbanController.extend({
        custom_events: _.extend({}, KanbanController.prototype.custom_events, {
            dashboard_open_action: '_onDashboardOpenAction',
        }),
    
        /**
         * @private
         * @param {OdooEvent} e
         */
        _onDashboardOpenAction: function (e) {
            return this.do_action(e.data.action_name,
                {additional_context: JSON.parse(e.data.action_context)});
        },
    });

    var StockLotKanbanDashboardView = KanbanView.extend({
        config: _.extend({}, KanbanView.prototype.config, {
            Model: StockLotKanbanDashboardModel,
            Renderer: StockLotKanbanDashboardRenderer,
            Controller: StockLotKanbanDashboardController,
        }),
    });

    //view_registry.add('rent_logistics_list_dashboard', RentLogisticsListDashboardView);
    view_registry.add('stock_lot_kanban_dashboard', StockLotKanbanDashboardView);

    return {
        //RentLogisticsListDashboardModel: RentLogisticsListDashboardModel,
        //RentLogisticsListDashboardRenderer: RentLogisticsListDashboardRenderer,
        //RentLogisticsListDashboardController: RentLogisticsListDashboardController,
        StockLotKanbanDashboardModel: StockLotKanbanDashboardModel,
        StockLotKanbanDashboardRenderer: StockLotKanbanDashboardRenderer,
        StockLotKanbanDashboardController: StockLotKanbanDashboardController
    }
});