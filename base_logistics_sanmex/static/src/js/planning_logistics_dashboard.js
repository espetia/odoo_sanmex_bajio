odoo.define('planning.logistics.dashboard', function (require) {
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
    SampleServer.mockRegistry.add('logistics.planning/retrieve_planning_dashboard', () => {
        return Object.assign({}, dashboardValues);
    });

    //--------------------------------------------------------------------------
    // List View
    //--------------------------------------------------------------------------

    var PlanningLogisticsListDashboardRenderer = ListRenderer.extend({
        events:_.extend({}, ListRenderer.prototype.events, {
            'click .o_dashboard_action': '_onDashboardActionClicked',
            'click .o_dashboard_action_rent': '_onDashboardActionClickedRent',
        }),
        /**
         * @override
         * @private
         * @returns {Promise}
         */
        _renderView: function () {
            var self = this;
            return this._super.apply(this, arguments).then(function () {
                var values = self.state.dashboardValues;
                var rentlog_dashboard = QWeb.render('base_logistics_sanmex.PlanningLogisticsDashboard', {
                    values: values,
                });
                self.$el.prepend(rentlog_dashboard);
                //console.log(self.$el.parent().find(".o_rent_logistics_dashboard.container"))
                //self.$el.parent().find(".o_rent_logistics_dashboard.container").remove();
                
                //self.$el.before(rentlog_dashboard);
            });
        },

        /**
         * @private
         * @param {MouseEvent}
         */
        _onDashboardActionClicked: function (e) {
            //console.log("Click action button")
            e.preventDefault();
            var $action = $(e.currentTarget);
            //console.log("Click action button")
            this.trigger_up('dashboard_open_action', {
                action_name: "base_logistics_sanmex.planning_logistics_action_dashboard_list",
                action_context: $action.attr('context'),
            });
        },
        _onDashboardActionClickedRent: function (e) {
            //console.log("Click action button")
            e.preventDefault();
            var $action = $(e.currentTarget);
            //console.log("Click action button")
            this.trigger_up('dashboard_open_action_rent', {
                action_name: "base_logistics_sanmex.logistics_rental_order_action",
                action_context: $action.attr('context'),
            });
        },
    });

    var PlanningLogisticsListDashboardModel = ListModel.extend({
        /**
         * @override
         */
        init: function () {
            this.dashboardValues = {};
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
                model: 'logistics.planning',
                method: 'retrieve_planning_dashboard',
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
    var PlanningLogisticsListDashboardController = ListController.extend({
        custom_events: _.extend({}, ListController.prototype.custom_events, {
            dashboard_open_action: '_onDashboardOpenAction',
            dashboard_open_action_rent: '_onDashboardOpenActionRent',
        }),
    
        /**
         * @private
         * @param {OdooEvent} e
         */
        _onDashboardOpenAction: function (e) {
            //console.log("Pruebas Consola")
            return this.do_action(e.data.action_name,
                {additional_context: JSON.parse(e.data.action_context)});
        },
        
        _onDashboardOpenActionRent: function (e) {
            //console.log("Pruebas Consola")
            return this.do_action(
                e.data.action_name,
                {additional_context: JSON.parse(e.data.action_context)}
                //{
                //    type: 'ir.actions.act_window',
                //    res_model: 'sale.order',
                //    name: 'Open',
                //    view_mode: 'form',
                //    views: [[false, 'form']],
                //    target: 'new',
                //    //context: JSON.parse(e.data.action_context)
                //}
            );
        },
    });
    
    var PlanningLogisticsListDashboardView = ListView.extend({
        config: _.extend({}, ListView.prototype.config, {
            Model: PlanningLogisticsListDashboardModel,
            Renderer: PlanningLogisticsListDashboardRenderer,
            Controller: PlanningLogisticsListDashboardController,
        }),
    });


    view_registry.add('planning_logistics_list_dashboard', PlanningLogisticsListDashboardView);

    return {
        PlanningLogisticsListDashboardModel: PlanningLogisticsListDashboardModel,
        PlanningLogisticsListDashboardRenderer: PlanningLogisticsListDashboardRenderer,
        PlanningLogisticsListDashboardController: PlanningLogisticsListDashboardController
    }
});