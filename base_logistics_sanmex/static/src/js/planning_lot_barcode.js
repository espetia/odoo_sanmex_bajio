/** @odoo-module **/

//import { FormRenderer } from "@web/views/form/form_renderer";
//const FormRenderer = require('web.FormRenderer')
import FormRenderer from 'web.FormRenderer';
import FormController from 'web.FormController';
var Dialog = require('web.Dialog');
import { useService } from "@web/core/utils/hooks";
import core from 'web.core';
var _t = core._t;
import rpc from 'web.rpc';
var beep = new Audio('/base_logistics_sanmex/static/src/audio/beep_scan.mp3');
import FormView from 'web.FormView';
import viewRegistry from 'web.view_registry';

var ComPlanningSanmexRenderer = FormRenderer.extend({
    events: _.extend({}, FormRenderer.prototype.events,{
        "click .o_barcode_button": '_PlanningBarcodeConsole',
        "click .o_qrcode_button": '_PlanningQRcode',
        }),
    /**
         * @override
         * @private
         * @returns {Promise}
         */
    _renderView: function () {
        var self = this;
        return this._super.apply(this, arguments).then(function () {
            
            var barcodeField = $(".barcode")
        
            //self.$el.parent().find(".o_rent_logistics_dashboard.container").remove();
            
            //self.$el.before(rentlog_dashboard);
        });
    },

    /**
     * @private
     * @param {MouseEvent}
     */
    //setup() {
    //    this.notification = useService("notification");
    //    super.setup();
    //},
    _PlanningQRcode: async function (event) {
        var self = this;

        function delay(time) {
            return new Promise(resolve => setTimeout(resolve, time));
        }
        var video = document.createElement('video');
        var reader = document.createElement('div');
        reader.setAttribute('id', 'barcode_id')
        //await navigator.mediaDevices.getUserMedia({ video: true })
        //.then(function (stream) {
        //    video.srcObject = stream;
        //    video.play();
        //    const dialog = new Dialog(this, {
        //        title: 'Barcode Scanner',
        //        buttons:
        //            [{
        //                text: _t('close'), classes: 'btn-primary', close: true, click: function () {
        //                    
        //                    dialog.close();
        //                    var tracks = video.srcObject.getTracks();
        //                        tracks.forEach(function(track) {
        //                            track.stop();
        //                        });
        //                }
        //            }],
        //        size: 'medium',
        //        $content: video,
        //        });
        //        dialog.open();
        //});
        const dialog = new Dialog(this, {
            title: 'Barcode Scanner',
                buttons:
                    [{
                        text: _t('close'), classes: 'btn-primary', close: true, click: function () {
                            
                            dialog.close();
                        }
                    }],
                size: 'medium',
                $content: reader,
        });
        dialog.open();
        await delay(1000);
        var scan_div = document.getElementById("barcode_id");
        console.log(scan_div)
        const scanner = new Html5QrcodeScanner('barcode_id', {
            qrbox: {
                width: 250,
                height: 250,
                },  // Sets dimensions of scanning box (set relative to reader element width)
            fps: 20, // Frames per second to attempt a scan
            formatsToSupport: [Html5QrcodeSupportedFormats.EAN_13, Html5QrcodeSupportedFormats.CODE_128, Html5QrcodeSupportedFormats.CODE_39, Html5QrcodeSupportedFormats.EAN_8,Html5QrcodeSupportedFormats.QR_CODE]
            });
        scanner.render(success, error);
        // Starts scanner
        function success(decodedText, decodedResult) {
            //const keyValuePairs = data.split(',');
            //const result = {};
            //for (const pair of keyValuePairs) {
            //    const [key, value] = pair.split(':');
            //    const trimmedKey = key.trim();
            //    const trimmedValue = value.trim();
            //    result[trimmedKey] = trimmedValue;
            //}
            console.log(`Scan result: ${decodedText}`, decodedResult);
            self.state.data.barcode = decodedText
            var info_test = {
                dataPointID: self.state.id,
                changes: {barcode: decodedText},
                viewType: "form",
                notifyChange: true
            };
            self.trigger_up('field_changed',info_test)
          
            beep.play();

            scanner.clear();
            dialog.close();
        }
        function error(err) {
            console.warn(err);// Prints any errors to the console
        }
    },

    _PlanningBarcodeConsole: async function (e) { 
        var self = this;
        //var load_params = self.props.record.__bm_load_params__;
        console.log("parametros---")
        console.log(self)
        var video = document.createElement('video');
        var code_result = ''
        
        video.setAttribute('id', 'barcode_id')
        await navigator.mediaDevices.getUserMedia({ video: true })
        .then(function (stream) {
            video.srcObject = stream;
            video.play();
            const dialog = new Dialog(this, {
            title: 'Barcode Scanner',
            buttons:
                [{
                    text: _t('close'), classes: 'btn-primary', close: true, click: function () {
                        Quagga.stop();
                        dialog.close();
                        var tracks = video.srcObject.getTracks();
                            tracks.forEach(function(track) {
                                track.stop();
                            });
                    }
                }],
            size: 'medium',
            $content: video,
            });
            dialog.open();
            Quagga.init({
                inputStream : {
                    name : "Live",
                    type : "LiveStream",
                    constraints: {
                        video: {
                            facingMode: {
                              exact: "environment"
                            }
                        }
                    },
                    numOfWorkers : navigator.hardwareConcurrency,
                    target : video
                },
                decoder: {
                   //readers : ['code_128_reader','ean_reader']
                   readers : ['ean_reader']
                }
            },
                function(err){
                    if(err){
                    console.log(err);
                    return
                    }
                    Quagga.start();
                }
            );
            var last_result=[];
            Quagga.onDetected(function(result){
                var last_code = result.codeResult.code;
                //console.log(last_code)
                code_result = last_code
                console.log('test...')
                console.log(code_result)
                self.state.data.barcode = last_code
                var info_test = {
                    dataPointID: self.state.id,
                    changes: {barcode: last_code},
                    viewType: "form",
                    notifyChange: true
                };
                self.trigger_up('field_changed',info_test);
                last_result.push(last_code);
                //self.do_action('reload');
                //self._trigger();
                last_result=[];
                beep.play();
                Quagga.stop();
                dialog.close();
                var tracks = video.srcObject.getTracks();
                    tracks.forEach(function(track) {
                    track.stop();
                });
                rpc.query({model: "sanmex.assign.rent.lot", method: "barcode_search", args: [[last_code]]
                })
                .then(function (data) {
                    if(data == true){
                        self.displayNotification({
                            title: _t("Product Not Found!"),
                            message: _t("Product with the scanned Barcode Not Found in the system"),
                            type: "danger",
                        });
                        //self.notification.add(self.env._t("Product with the scanned Barcode Not Found in the system"), {
                        //    title: self.env._t("Product Not Found!"),
                        //    type: "danger",
                        //});
                    }
                });
            });
        });
        console.log("despues de escanear")
        console.log(code_result)
    },
    
});

var ComPlanningSanmexController = FormController.extend({
    _PlanningBarcodeConsole: function () { 
        console.log("click console")
    },
})

var PlanningBarcodeView = FormView.extend({
    config: _.extend({}, FormView.prototype.config, {
        Renderer: ComPlanningSanmexRenderer,
        Controller: ComPlanningSanmexController,
    }),
});

viewRegistry.add('planning_barcode', PlanningBarcodeView);
export default {
PlanningBarcodeView: PlanningBarcodeView,
ComPlanningSanmexRenderer: ComPlanningSanmexRenderer,
};
