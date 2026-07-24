import { useEffect, useState } from "react";
import { Heart, Sparkles, Trash2 } from "lucide-react";
import API from "../api/api";

export default function Recommendations() {
  const [items, setItems] = useState([]);
  const [memory, setMemory] = useState([]);
  const [form, setForm] = useState({ key: "brand", value: "" });
  const [message, setMessage] = useState("");

  const load = async () => {
    const [recommendations, preferences] = await Promise.all([API.get("/recommendations"), API.get("/memory")]);
    setItems(recommendations.data); setMemory(preferences.data);
  };
  useEffect(() => {
    Promise.all([API.get("/recommendations"), API.get("/memory")])
      .then(([recommendations, preferences]) => {
        setItems(recommendations.data); setMemory(preferences.data);
      })
      .catch(() => setMessage("Could not load personalized recommendations."));
  }, []);

  const save = async (event) => {
    event.preventDefault();
    await API.put("/memory", form); setForm({ ...form, value: "" }); setMessage("Preference saved. Recommendations have been refreshed."); await load();
  };
  const remove = async (key) => { await API.delete(`/memory/${encodeURIComponent(key)}`); await load(); };

  return <div>
    <div className="page-heading"><div><span className="eyebrow">Hybrid recommendation engine</span><h1>For You</h1><p>Recommendations combine your saved preferences, wishlist, purchase categories, ratings, and live availability.</p></div></div>
    {message && <p className="notice">{message}</p>}
    <section className="preference-panel">
      <div><h2>Shopping memory</h2><p>Save preferences the assistant can use across conversations.</p></div>
      <form onSubmit={save} className="preference-form">
        <select value={form.key} onChange={(e) => setForm({ ...form, key: e.target.value })}><option value="brand">Preferred brand</option><option value="budget">Maximum budget</option><option value="size">Size</option><option value="color">Color</option><option value="use_case">Use case</option></select>
        <input required placeholder="Preference value" value={form.value} onChange={(e) => setForm({ ...form, value: e.target.value })}/><button>Remember</button>
      </form>
      <div className="memory-chips">{memory.map((item) => <span key={item.id}><b>{item.key}:</b> {item.value}<button aria-label={`Delete ${item.key}`} onClick={() => remove(item.key)}><Trash2 size={13}/></button></span>)}</div>
    </section>
    <div className="recommendation-grid">{items.map((item) => <article key={item.product.id} className="recommendation-card">
      <div className="recommendation-icon"><Sparkles size={20}/></div><h3>{item.product.name}</h3><p>{item.reason}</p><div className="recommendation-meta"><strong>${Number(item.product.price).toFixed(2)}</strong><span>{item.product.rating || 0} ★</span><span>{item.product.stock_quantity} in stock</span></div>
      <button onClick={() => API.post("/wishlist", { product_id: item.product.id }).then(() => setMessage(`${item.product.name} saved to your wishlist.`))}><Heart size={16}/> Save</button>
    </article>)}</div>
    {!items.length && <div className="empty-panel"><Sparkles/><h2>Teach the assistant what you like</h2><p>Add a preferred brand or budget, save wishlist products, or place an order to generate recommendations.</p></div>}
  </div>;
}
