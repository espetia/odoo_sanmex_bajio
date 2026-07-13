/** @odoo-module */

import { registry } from "@web/core/registry"
import { KpiCard } from "./kpi_card/kpi_card"
import { ChartRenderer } from "./chart_renderer/chart_renderer"
import { useService } from "@web/core/utils/hooks"
import { loadJS } from "@web/core/assets"
import { getColor } from "@web/views/graph/colors"
import { browser } from "@web/core/browser/browser"
import { routeToUrl } from "@web/core/browser/router_service"

const { Component, useState } = owl
const { useRef, onMounted, onWillStart } = owl.hooks

export class OwlSalesDashboard extends Component {
    //top Products
    async getTopProducts(){
        let domain = [['state', 'in',['sale','done']]]
        if (this.state.period > 0){
            domain.push(['date','>',this.state.current_date])
        }
        const data = await this.orm.readGroup("sale.report", domain,['product_id','price_total'],['product_id'],{limit:5, orderby:"price_total desc"})
        //console.log(data)
        this.state.topProducts = {
                data: {
                    labels: data.map(d=>d.product_id[1]),
                    datasets: [
                        {
                        label: 'Total',
                        data: data.map(d=>d.price_total),
                        hoverOffset: 4,
                        backgroundColor: data.map((_, index)=>getColor(index))
                    },{
                        label: 'Count',
                        data: data.map(d=>d.product_id_count),
                        hoverOffset: 4,
                        backgroundColor: data.map((_, index)=>getColor(index))
                    }
                    ]
                },
                domain,
                label_field: 'product_id',
        }
    }
    //Top sales People
    async getTopSalesPeople(){
        let domain = [['state', 'in',['sale','done']]]
        if (this.state.period > 0){
            domain.push(['date','>',this.state.current_date])
        }
        const data = await this.orm.readGroup("sale.report", domain,['user_id','price_total'],['user_id'],{limit:5, orderby:"price_total desc"})
        //console.log(data)
        this.state.topSalesPeople = {
                data: {
                    labels: data.map(d=>d.user_id[1]),
                    datasets: [
                        {
                        label: 'Total',
                        data: data.map(d=>d.price_total),
                        hoverOffset: 4,
                        backgroundColor: data.map((_, index)=>getColor(index))
                    }
                    ]
                },
                domain,
                label_field: 'user_id',
        }
    }
    //Monthly sales
    async getMonthlySales(){
        
        let domain = [['state', 'in',['draft','sent','sale','done']]]
        if (this.state.period > 0){
            domain.push(['date','>',this.state.current_date])
        }
        const data = await this.orm.readGroup("sale.report", domain,['date','state','price_total'],['date','state'],{orderby:"date", lazy: false})
        const labels = [... new Set(data.map(d=>d.date))]
        const quotations = data.filter(d => d.state == 'draft' || d.state == 'sent')
        const orders = data.filter(d => ['sale', 'done'].includes(d.state))
        
        console.log(data)
        this.state.monthlySales = {
                data: {
                    labels: labels,
                    datasets: [
                        {
                        label: 'Quotations',
                        data: labels.map(l=>quotations.filter(q=>l==q.date).map(j=>j.price_total).reduce((a,c)=>a+c,0)),
                        hoverOffset: 4,
                        backgroundColor: "red",
                    },{
                        label: 'Orders',
                        data: labels.map(l=>orders.filter(q=>l==q.date).map(j=>j.price_total).reduce((a,c)=>a+c,0)),
                        hoverOffset: 4,
                        backgroundColor: "green",
                    }
                    ]
                },
                domain,
                label_field: 'date',
        }
    }
    //Partner orders
    async getPartnerOrders(){
        let domain = [['state', 'in',['draft','sent','sale','done']]]
        if (this.state.period > 0){
            domain.push(['date','>',this.state.current_date])
        }
        const data = await this.orm.readGroup("sale.report", domain,['partner_id','price_total','product_uom_qty'],['partner_id'],{orderby:"partner_id", lazy: false})
        console.log(data)
        this.state.partnerOrders = {
                data: {
                    labels: data.map(d=>d.partner_id[1]),
                    datasets: [
                        {
                        label: 'Total Amount',
                        data: data.map(d=>d.price_total),
                        hoverOffset: 4,
                        backgroundColor: "orange",
                        yAxisID:'Total',
                        order:1,
                    },{
                        label: 'Ordered Qty',
                        data: data.map(d=>d.product_uom_qty),
                        hoverOffset: 4,
                        backgroundColor: "blue",
                        type: "line",
                        borderColor: "blue",
                        yAxisID:'Qty',
                        order:0,
                    }
                    ]
                },
                    scales:{
                        Qty: {
                            position: 'right',
                        }
                        //yAxes:[
                        //    {id:'Qty', position:'right', type: 'linear',},
                        //    {id:'Total', position:'left', type: 'linear',}
                        //]
                    },
                domain,
                label_field: 'partner_id',
        }
    }
    setup() {
        this.state = useState({
            quotations:{
                value:10,
                percentage:10,
            },
            period:90,
            number_p:0,
        });
        this.state.topProducts = {}
        this.orm = useService("orm")
        this.actionService = useService("action")

        const old_chart_js = document.querySelector('script[src="/web/static/lib/Chart/Chart.js"')
        const router = useService("router")

        if (old_chart_js) {
            let { search, hash } = router.current
            search.old_chart_js = old_chart_js != null ? "0":"1"
            //hash.action = 467
            browser.location.href = browser.location.origin + routeToUrl(router.current)
        }
        onWillStart(async ()=>{
            this.getDates()
            await this.getQuotations()
            await this.getOrders()

            await this.getTopProducts()
            await this.getTopSalesPeople()
            await this.getMonthlySales()
            await this.getPartnerOrders()
             
        })
    }
    async onChangePeriod(event){
        this.state.period = event.target.value
        
        console.log(this.state.period);
        console.log(moment().subtract(this.state.period, 'days').format('L'))
        this.getDates()
        await this.getQuotations()
        await this.getOrders()

        await this.getTopProducts()
        await this.getTopSalesPeople()
        await this.getMonthlySales()
        await this.getPartnerOrders()
    } 

    getDates(){
        this.state.current_date = moment().subtract(this.state.period, 'days').format()
        this.state.previous_date = moment().subtract(this.state.period * 2, 'days').format()
    }

    async getQuotations(){
        let domain = [['state', 'in',['sent','draft']]]
        if (this.state.period >0){
            domain.push(['date_order','>',this.state.current_date])
        }
        const data = await this.orm.search("sale.order", domain)
        this.state.quotations.value = data.length
       
        //previous period
        let prev_domain = [['state', 'in',['sent','draft']]]
        if (this.state.period >0){
            prev_domain.push(['date_order','>',this.state.previous_date], ['date_order','<=', this.state.current_date])
        }
        const prev_data = await this.orm.search("sale.order", prev_domain)
        const percentage = ((data.length - prev_data.length) / prev_data.length) * 100
        this.state.quotations.percentage = percentage
        //console.log(this.state.current_date, this.state.previous_date)
        //console.log(percentage)
    }

    async getOrders(){
        let domain = [['state', 'in',['sale','done']]]
        if (this.state.period >0){
            domain.push(['date_order','>',this.state.current_date])
        }
        const data = await this.orm.search("sale.order", domain)
        //this.state.orders.value = data.length
       
        //previous period
        let prev_domain = [['state', 'in',['sale','done']]]
        if (this.state.period >0){
            prev_domain.push(['date_order','>',this.state.previous_date], ['date_order','<=', this.state.current_date])
        }
        const prev_data = await this.orm.search("sale.order", prev_domain)
        const percentage = ((data.length - prev_data.length) / prev_data.length) * 100
        //this.state.orders.percentage = percentage

        //revenue
        const current_revenue = await this.orm.readGroup("sale.order", domain,["amount_total:sum"], [])
        const prev_revenue = await this.orm.readGroup("sale.order", prev_domain,["amount_total:sum"], [])
        const current_revenue_percentage = ((current_revenue[0].amount_total - prev_revenue[0].amount_total) / prev_revenue[0].amount_total) * 100

        //average
        const current_average = await this.orm.readGroup("sale.order", domain,["amount_total:avg"], [])
        const prev_average = await this.orm.readGroup("sale.order", prev_domain,["amount_total:avg"], [])
        const average_percentage = ((current_average[0].amount_total - prev_average[0].amount_total) / prev_average[0].amount_total) * 100
        console.log(current_revenue)
        this.state.orders = {
            value: data.length,
            percentage: percentage.toFixed(2),
            revenue: `$${(current_revenue[0].amount_total/1000).toFixed(2)}K`,
            revenue_percentage: current_revenue_percentage.toFixed(2),
            average: `$${(current_average[0].amount_total/1000).toFixed(2)}K`,
            average_percentage: average_percentage.toFixed(2),
        }
    }
    async viewQuotations(){
        let domain = [['state', 'in', ['sent', 'draft']]]
        if (this.state.period > 0){
            domain.push(['date_order','>', this.state.current_date])
        }
        let list_view = await this.orm.searchRead("ir.model.data", [['name', '=', 'view_quotation_tree_with_onboarding']], ['res_id'])

        this.actionService.doAction({
            type: "ir.actions.act_window",
            name: "Quotations",
            res_model: "sale.order",
            domain,
            views: [
                [list_view.length > 0 ? list_view[0].res_id : false, "list"],
                [false, "form"],
            ]
        })
    }
    viewOrders(){
        let domain = [['state', 'in', ['sale', 'done']]]
        if (this.state.period > 0){
            domain.push(['date_order','>', this.state.current_date])
        }
        

        this.actionService.doAction({
            type: "ir.actions.act_window",
            name: "Orders",
            res_model: "sale.order",
            domain,
            context:{group_by:['date_order']},
            views: [
                [false, "list"],
                [false, "form"],
            ]
        })
    }
    viewRevenues(){
        let domain = [['state', 'in', ['sale', 'done']]]
        if (this.state.period > 0){
            domain.push(['date_order','>', this.state.current_date])
        }
        

        this.actionService.doAction({
            type: "ir.actions.act_window",
            name: "Orders",
            res_model: "sale.order",
            domain,
            context:{group_by:['date_order','partner_id']},
            views: [
                [false, "pivot"],
                [false, "form"],
            ]
        })
    }
}

OwlSalesDashboard.template="custom_dashboard.OwlSalesDashboard";
OwlSalesDashboard.components = { KpiCard, ChartRenderer }
registry.category("actions").add("custom_dashboard.sales_dashboard", OwlSalesDashboard);
