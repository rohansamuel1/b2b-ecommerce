import { useEffect, useState } from "react";
import { Bar, BarChart, CartesianGrid, ResponsiveContainer, Tooltip, XAxis, YAxis } from "recharts";
import API from "../api/api";

export default function Analytics() {
  const [vendors,setVendors]=useState([]); const [insights,setInsights]=useState({category_revenue:[],top_products:[],order_statuses:[],returns:[]});
  useEffect(()=>{Promise.all([API.get("/analytics/vendors"),API.get("/analytics/intelligence")]).then(([v,i])=>{setVendors(v.data);setInsights(i.data)}).catch(console.error);},[]);
  return <div><div className="page-heading"><div><span className="eyebrow">Business intelligence</span><h1>Analytics</h1><p>Revenue, product performance, operational status, and return activity from transactional data.</p></div></div>
    <div className="analytics-grid"><section><h2>Revenue by category</h2><ResponsiveContainer width="100%" height={260}><BarChart data={insights.category_revenue}><CartesianGrid strokeDasharray="3 3"/><XAxis dataKey="category"/><YAxis/><Tooltip/><Bar dataKey="revenue" fill="#2563eb" radius={[6,6,0,0]}/></BarChart></ResponsiveContainer></section><section><h2>Order status</h2><ResponsiveContainer width="100%" height={260}><BarChart data={insights.order_statuses}><CartesianGrid strokeDasharray="3 3"/><XAxis dataKey="status"/><YAxis allowDecimals={false}/><Tooltip/><Bar dataKey="count" fill="#0891b2" radius={[6,6,0,0]}/></BarChart></ResponsiveContainer></section></div>
    <h2>Top products</h2><table className="data-table"><thead><tr><th>Product</th><th>Units</th><th>Revenue</th></tr></thead><tbody>{insights.top_products.map(x=><tr key={x.product_id}><td>{x.product}</td><td>{x.units}</td><td>${x.revenue.toFixed(2)}</td></tr>)}</tbody></table>
    <h2 style={{marginTop:28}}>Vendor performance</h2><table className="data-table"><thead><tr><th>Vendor</th><th>Revenue</th><th>Orders</th></tr></thead><tbody>{vendors.map(v=><tr key={v.vendor_id}><td>{v.company_name}</td><td>${Number(v.revenue).toFixed(2)}</td><td>{v.orders}</td></tr>)}</tbody></table>
  </div>;
}
