/** @odoo-module **/

import { registry } from "@web/core/registry"
import { loadAssets, useAssets } from "@web/core/assets"
const { Component } = owl
const { useRef, onMounted, onWillUnmount, onWillStart } = owl.hooks
import { useService, useEffect } from "@web/core/utils/hooks"

export class ChartRenderer extends Component {
    setup() {
        // initialize component here
        this.chartRef = useRef("chart")
        
        this.actionService = useService("action")
        //useAssets({ jsLibs: ["/web/static/lib/Chart/Chart.js"] });

        onWillStart(async ()=>{
            //await loadJS("https://cdnjs.cloudflare.com/ajax/libs/Chart.js/4.4.0/chart.umd.min.js")
            //await loadJS("/web/static/lib/Chart/Chart.js")
            await loadAssets({ jsLibs: ["https://cdnjs.cloudflare.com/ajax/libs/Chart.js/4.4.1/chart.umd.min.js"] });
           // await loadAssets({ jsLibs: ["/web/static/lib/Chart/Chart.js"] });
            //useAssets({ jsLibs: ["/web/static/lib/Chart/Chart.js"] });
        })

        useEffect(()=>{
            //console.log("ha cambiado de estado")
            this.renderChart()
        },()=>[this.props.data])

        onMounted(()=> this.renderChart())
        onWillUnmount(()=>{
            if (this.chart){
            this.chart.destroy()
            }
        })
    }
    remplaceMonths(ptext) {
        var regex = /\b(enero|febrero|marzo|abril|mayo|junio|julio|agosto|septiembre|octubre|noviembre|diciembre)\b/gi;
        return ptext.replace(regex, function(match) {
            var monthsTranslate = {
                "enero": "January", "febrero": "February", "marzo": "March", "abril": "April", "mayo": "May", "junio": "June",
                "julio": "July", "agosto": "August", "septiembre": "September", "octubre": "October", "noviembre": "November", "diciembre": "December"
            };
            console.log(monthsTranslate[match.toLowerCase()])
            return monthsTranslate[match.toLowerCase()];
        });
    }
    renderChart(){
        const old_chartjs = document.querySelector('script[src="/web/static/lib/Chart/Chart.js"]')

        if (old_chartjs){
            return
        }
        if (this.chart){
            this.chart.destroy()
        }
        this.chart = new Chart(this.chartRef.el,
            {
            type: this.props.type,
            data: this.props.data,
            options: {
                    onClick: (e)=>{
                        const active = e.chart.getActiveElements()
                        //console.log(active)
                        
                        if (active.length > 0){
                            const label = e.chart.data.labels[active[0].index]
                            console.log(label)
                            const dataset = e.chart.data.datasets[active[0].datasetIndex].label
                            
                            const { label_field, domain } = this.props
                            let new_domain = domain ? domain : []

                            if(label_field){
                                if (label_field.includes('date')){

                                    const labeltrans = this.remplaceMonths(label);
                                    console.log(labeltrans)
                                    const timeStamp = Date.parse(labeltrans)
                                    const selected_month = moment(timeStamp)
                                    console.log(selected_month)
                                    const month_start = selected_month.format()
                                    const month_end = selected_month.endOf('month').format()
                                    //console.log(month_end)
                                    new_domain.push(['date','>=',month_start], ['date','<=',month_end])
                                    console.log(new_domain)
                                }
                                else{
                                    new_domain.push([label_field, '=', label])
                                    //console.log(new_domain)
                                }

                                
                            }

                            if (dataset == 'Quotations') {
                                new_domain.push(['state', 'in', ['draft','sent']])
                            }

                            if (dataset == 'Orders' ){
                                new_domain.push(['state', 'in', ['sale','done']])
                            }

                            this.actionService.doAction({
                                type: "ir.actions.act_window",
                                name: this.props.title,
                                res_model: "sale.report",
                                domain: new_domain,
                                views:[
                                    [false, "list"],
                                    [false, "form"],
                                ],
                            })
                        }
                        //console.log(label)
                    },
                    responsive: true,
                    plugins: {
                        legend:{
                            position: 'bottom',
                        },
                        title: {
                            display: true,
                            text: this.props.title,
                            position: 'bottom',
                        }
                    },
                    scales: 'scales' in this.props ? this.props.scales : {},
                }
            }
        );
    }

    
}

ChartRenderer.template="custom_dashboard.ChartRenderer";
