import { useEffect, useState } from "react";
import { BookOpen, FileText } from "lucide-react";
import API from "../api/api";

export default function KnowledgeBase() {
  const [documents,setDocuments]=useState([]); const [products,setProducts]=useState([]); const [message,setMessage]=useState("");
  const [form,setForm]=useState({product_id:"",title:"",document_type:"manual",content:"",source_url:""});
  const load=()=>Promise.all([API.get("/knowledge/documents"),API.get("/products")]).then(([d,p])=>{setDocuments(d.data);setProducts(p.data)});
  useEffect(()=>{load().catch(()=>setMessage("Could not load the knowledge base."));},[]);
  const submit=async(e)=>{e.preventDefault();await API.post("/knowledge/documents",{...form,product_id:form.product_id?Number(form.product_id):null});setForm({product_id:"",title:"",document_type:"manual",content:"",source_url:""});setMessage("Document indexed for assistant retrieval.");await load();};
  return <div><div className="page-heading"><div><span className="eyebrow">Retrieval-augmented generation</span><h1>Knowledge Base</h1><p>Add manuals, warranty terms, specifications, FAQs, and policies that the AI can retrieve before answering.</p></div></div>
    {message&&<p className="notice">{message}</p>}
    <form className="knowledge-form" onSubmit={submit}><select value={form.product_id} onChange={e=>setForm({...form,product_id:e.target.value})}><option value="">General policy</option>{products.map(p=><option key={p.id} value={p.id}>{p.name}</option>)}</select><input required placeholder="Document title" value={form.title} onChange={e=>setForm({...form,title:e.target.value})}/><select value={form.document_type} onChange={e=>setForm({...form,document_type:e.target.value})}><option>manual</option><option>warranty</option><option>specification</option><option>faq</option><option>policy</option></select><input placeholder="Source URL (optional)" value={form.source_url} onChange={e=>setForm({...form,source_url:e.target.value})}/><textarea required minLength="20" placeholder="Paste document content here..." value={form.content} onChange={e=>setForm({...form,content:e.target.value})}/><button><BookOpen size={16}/> Add to knowledge base</button></form>
    <div className="document-list">{documents.map(d=><article key={d.id}><FileText/><div><h3>{d.title}</h3><p>{d.document_type} · {d.product_id?`Product ${d.product_id}`:"General"}</p><small>{d.content.slice(0,180)}{d.content.length>180?"…":""}</small></div></article>)}</div>
  </div>;
}
