odoo.define('san_mex_company_custom.CustomerStatusDashboard', function (require) {
    "use strict";

    const ListController = require('web.ListController');
    const ListView = require('web.ListView');
    const viewRegistry = require('web.view_registry');
    const qweb = require('web.core').qweb;

    const CustomerStatusListController = ListController.extend({
        custom_events: _.extend({}, ListController.prototype.custom_events, {
            'dashboard_refresh': '_onDashboardRefresh',
        }),

        /**
         * @override
         */
        willStart: function () {
            const self = this;
            this.stats = {};
            const statsDef = this._rpc({
                model: 'customer.status.log',
                method: 'get_stats',
            }).then(function (result) {
                self.stats = result;
            });
            return Promise.all([this._super.apply(this, arguments), statsDef]);
        },

        /**
         * @override
         */
        renderButtons: function ($node) {
            this._super.apply(this, arguments);
            if (this.$buttons) {
                this._renderDashboard();
            }
        },

        _renderDashboard: function () {
            const self = this;
            const $dashboard = $(qweb.render('san_mex_company_custom.CustomerStatusDashboard', {
                stats: this.stats,
            }));
            $dashboard.find('.o_stat_box').on('click', function (ev) {
                const type = $(ev.currentTarget).data('type');
                self._onStatClick(type);
            });
            this.$el.prepend($dashboard);
        },

        _onStatClick: function (type) {
            let domain = [];
            const today = new Date();
            const firstDayMonth = new Date(today.getFullYear(), today.getMonth(), 1);
            const firstDayMonthStr = moment(firstDayMonth).format('YYYY-MM-DD');

            if (type === 'new_month') {
                domain = [['status_type', '=', 'new'], ['date_detected', '>=', firstDayMonthStr]];
            } else if (type === 'recovered_month') {
                domain = [['status_type', '=', 'recovered'], ['date_detected', '>=', firstDayMonthStr]];
            } else if (type === 'new_total') {
                domain = [['status_type', '=', 'new']];
            } else if (type === 'recovered_total') {
                domain = [['status_type', '=', 'recovered']];
            }
            this.reload({ domain: domain });
        },

        _onDashboardRefresh: function () {
            const self = this;
            this._rpc({
                model: 'customer.status.log',
                method: 'get_stats',
            }).then(function (result) {
                self.stats = result;
                self.$('.o_customer_status_dashboard').replaceWith(qweb.render('san_mex_company_custom.CustomerStatusDashboard', {
                    stats: self.stats,
                }));
                // Re-bind events
                self.$('.o_stat_box').on('click', function (ev) {
                    const type = $(ev.currentTarget).data('type');
                    self._onStatClick(type);
                });
            });
        },
    });

    const CustomerStatusListView = ListView.extend({
        config: _.extend({}, ListView.prototype.config, {
            Controller: CustomerStatusListController,
        }),
    });

    viewRegistry.add('customer_status_dashboard', CustomerStatusListView);

    return CustomerStatusListController;
});
