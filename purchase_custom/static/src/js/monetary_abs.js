odoo.define('purchase_custom.monetary_abs', function (require) {
"use strict";

var basic_fields = require('web.basic_fields');
var registry = require('web.field_registry');

var FieldMonetaryAbs = basic_fields.FieldMonetary.extend({
    _renderReadonly: function () {
        var old_val = this.value;
        this.value = Math.abs(this.value);
        this._super.apply(this, arguments);
        this.value = old_val;
    }
});

registry.add('monetary_abs', FieldMonetaryAbs);

return FieldMonetaryAbs;

});