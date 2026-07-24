import { useEffect, useMemo, useState } from "react";
import { CreditCard, LockKeyhole, Heart, Search } from "lucide-react";
import { useNavigate } from "react-router-dom";
import API from "../api/api";
import { getStoredUser } from "../auth";

function Products() {
  const navigate = useNavigate();
  const user = getStoredUser();
  const isAdmin = user?.role === "admin";
  const isStorefront = !isAdmin;
  const cartKey = `cart:${user?.id || "guest"}`;

  const [products, setProducts] = useState([]);
  const [search, setSearch] = useState("");
  const [cart, setCart] = useState(() => {
    try {
      return JSON.parse(localStorage.getItem(cartKey)) || {};
    } catch {
      return {};
    }
  });
  const [error, setError] = useState("");
  const [submitting, setSubmitting] = useState(false);
  const [paymentStatus, setPaymentStatus] = useState("");
  const [payment, setPayment] = useState({
    cardholder_name: user?.name || "",
    card_number: "4242 4242 4242 4242",
    expiry: "12/30",
    cvc: "123",
  });
  const [couponCode, setCouponCode] = useState("");
  const [form, setForm] = useState({
    name: "",
    description: "",
    sku: "",
    price: "",
    image_url: "",
    vendor_id: "",
    stock_quantity: "",
    reorder_level: "10",
  });

  async function loadProducts() {
    try {
      const response = await API.get("/products");
      setProducts(response.data);
    } catch (requestError) {
      setError(requestError.response?.data?.detail || "Could not load products.");
    }
  }

  useEffect(() => {
    API.get("/products")
      .then((response) => setProducts(response.data))
      .catch((requestError) => setError(
        requestError.response?.data?.detail || "Could not load products.",
      ));
  }, []);

  useEffect(() => {
    localStorage.setItem(cartKey, JSON.stringify(cart));
  }, [cart, cartKey]);

  const cartItems = useMemo(() => products
    .filter((product) => cart[product.id])
    .map((product) => ({ ...product, quantity: cart[product.id] })), [cart, products]);

  const cartTotal = cartItems.reduce(
    (total, product) => total + product.price * product.quantity,
    0,
  );

  const handleChange = (event) => {
    setForm({ ...form, [event.target.name]: event.target.value });
  };

  const handlePaymentChange = (event) => {
    setPayment({ ...payment, [event.target.name]: event.target.value });
  };

  const createProduct = async (event) => {
    event.preventDefault();
    setError("");
    try {
      await API.post("/products", {
        name: form.name,
        description: form.description,
        sku: form.sku,
        price: Number(form.price),
        image_url: form.image_url,
        vendor_id: Number(form.vendor_id),
        stock_quantity: Number(form.stock_quantity),
        reorder_level: Number(form.reorder_level),
      });
      setForm({
        name: "", description: "", sku: "", price: "", image_url: "", vendor_id: "",
        stock_quantity: "", reorder_level: "10",
      });
      loadProducts();
    } catch (requestError) {
      setError(requestError.response?.data?.detail || "Could not create product.");
    }
  };

  const requestLogin = () => {
    navigate("/login");
  };

  const updateCart = (product, quantity) => {
    if (!user) {
      requestLogin();
      return;
    }

    const nextQuantity = Math.max(0, Math.min(quantity, product.stock_quantity));
    setCart((current) => {
      const next = { ...current };
      if (nextQuantity === 0) delete next[product.id];
      else next[product.id] = nextQuantity;
      return next;
    });
  };

  const buyNow = (product) => {
    if (!user) {
      requestLogin();
      return;
    }

    updateCart(product, 1);
  };

  const saveToWishlist = async (product) => {
    if (!user) return requestLogin();
    try { await API.post("/wishlist", { product_id: product.id }); setPaymentStatus(`${product.name} saved to your wishlist.`); }
    catch (requestError) { setError(requestError.response?.data?.detail || "Could not update wishlist."); }
  };

  const productImage = (product) => (
    product.image_url ? (
      <img
        src={product.image_url}
        alt={product.name}
        style={{ width: "100%", height: "100%", objectFit: "cover", display: "block" }}
      />
    ) : (
      <div style={{
        display: "grid",
        placeItems: "center",
        width: "100%",
        height: "100%",
        background: "linear-gradient(135deg, #fafafa, #fff7df)",
        color: "#d98505",
        fontFamily: "\"Inter\", system-ui, sans-serif",
        fontSize: "42px",
        fontWeight: 800,
      }}>
        {product.name?.trim()?.[0] || "P"}
      </div>
    )
  );

  const checkout = async () => {
    if (!user) {
      requestLogin();
      return;
    }

    if (!cartItems.length) return;
    setSubmitting(true);
    setError("");
    setPaymentStatus("Contacting dummy Stripe...");
    try {
      const cardNumber = payment.card_number.replace(/\s/g, "");
      if (!payment.cardholder_name.trim()) {
        throw new Error("Cardholder name is required.");
      }
      if (!/^\d{12,19}$/.test(cardNumber)) {
        throw new Error("Enter a valid dummy Stripe card number.");
      }
      if (!/^\d{2}\/\d{2}$/.test(payment.expiry)) {
        throw new Error("Use MM/YY for the dummy Stripe expiry.");
      }
      if (!/^\d{3,4}$/.test(payment.cvc)) {
        throw new Error("Enter a valid dummy Stripe CVC.");
      }

      await new Promise((resolve) => setTimeout(resolve, 650));
      setPaymentStatus("Dummy Stripe payment approved.");

      const response = await API.post("/orders", {
        buyer_id: user.id,
        items: cartItems.map((item) => ({
          product_id: item.id,
          quantity: item.quantity,
        })),
        coupon_code: couponCode.trim() || null,
        payment_method: {
          provider: "stripe",
          ...payment,
        },
      });
      setCart({});
      localStorage.removeItem(cartKey);
      navigate(`/orders?placed=${response.data.id}`);
    } catch (requestError) {
      setError(requestError.response?.data?.detail || requestError.message || "Checkout failed. Please try again.");
      setPaymentStatus("");
      loadProducts();
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <div>
      <div className={isStorefront ? "storefront-hero" : undefined}>
        <div>
          {isStorefront && <span className="eyebrow">Public marketplace</span>}
          <h1>{isStorefront ? "Shop business essentials" : "Products"}</h1>
          {isStorefront && (
            <p>
              Browse the catalog without signing in. Login is required when you add products
              to your cart, buy now, or checkout.
            </p>
          )}
        </div>
      </div>
      {error && <p style={{ color: "#b42318", background: "#fef3f2", padding: "12px", borderRadius: "12px" }}>{error}</p>}
      <div className="catalog-search"><Search size={18}/><input value={search} onChange={(e) => setSearch(e.target.value)} placeholder="Search by product, SKU, description, or brand"/></div>

      {isAdmin && (
        <form onSubmit={createProduct} style={{
          background: "white", padding: "20px", borderRadius: "20px",
          marginTop: "20px", marginBottom: "24px", boxShadow: "0 2px 10px rgba(0,0,0,0.08)",
          display: "grid", gridTemplateColumns: "repeat(3, minmax(0, 1fr))", gap: "12px",
        }}>
          <div><label htmlFor="product-name">Product name</label><input id="product-name" required name="name" value={form.name} onChange={handleChange} /></div>
          <div><label htmlFor="product-description">Description</label><input id="product-description" name="description" value={form.description} onChange={handleChange} /></div>
          <div><label htmlFor="product-sku">SKU</label><input id="product-sku" required name="sku" value={form.sku} onChange={handleChange} /></div>
          <div><label htmlFor="product-price">Unit price</label><input id="product-price" required min="0" step="0.01" type="number" name="price" value={form.price} onChange={handleChange} /></div>
          <div><label htmlFor="product-image">Image URL</label><input id="product-image" name="image_url" value={form.image_url} onChange={handleChange} placeholder="/images/products/item.png" /></div>
          <div><label htmlFor="product-vendor">Vendor ID</label><input id="product-vendor" required min="1" type="number" name="vendor_id" value={form.vendor_id} onChange={handleChange} /></div>
          <div><label htmlFor="product-stock">Stock quantity</label><input id="product-stock" required min="0" type="number" name="stock_quantity" value={form.stock_quantity} onChange={handleChange} /></div>
          <div><label htmlFor="product-reorder">Reorder level</label><input id="product-reorder" required min="0" type="number" name="reorder_level" value={form.reorder_level} onChange={handleChange} /></div>
          <button type="submit" style={{ border: "none", padding: "12px", fontWeight: "bold" }}>
            Add Product
          </button>
        </form>
      )}

      {isStorefront ? (
        <div style={{ display: "grid", gridTemplateColumns: "minmax(0, 2fr) minmax(280px, 1fr)", gap: "24px", marginTop: "24px", alignItems: "start" }}>
          <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(220px, 1fr))", gap: "16px" }}>
            {products.filter((product) => `${product.name} ${product.description || ""} ${product.sku || ""} ${product.brand || ""}`.toLowerCase().includes(search.toLowerCase())).map((product) => (
              <article key={product.id} style={{ background: "white", padding: "14px", borderRadius: "20px", boxShadow: "0 4px 8px -1px rgba(0,0,0,0.10)" }}>
                <div style={{ aspectRatio: "1 / 1", overflow: "hidden", borderRadius: "16px", background: "#f5f5f5", marginBottom: "16px" }}>
                  {productImage(product)}
                </div>
                <h3 style={{ marginTop: 0 }}>{product.name}</h3>
                <p style={{ minHeight: "42px" }}>{product.description || "No description available."}</p>
                <p><strong>${Number(product.price).toFixed(2)}</strong></p>
                <small style={{ color: product.stock_quantity > 0 ? "#067647" : "#b42318" }}>
                  {product.stock_quantity > 0 ? `${product.stock_quantity} available` : "Out of stock"}
                </small>
                <button
                  disabled={product.stock_quantity < 1 || cart[product.id] >= product.stock_quantity}
                  onClick={() => updateCart(product, (cart[product.id] || 0) + 1)}
                  style={{ width: "100%", marginTop: "16px", padding: "10px", border: "none", cursor: product.stock_quantity > 0 ? "pointer" : "not-allowed" }}
                >
                  {!user ? "Login to add to cart" : cart[product.id] ? "Add another" : "Add to cart"}
                </button>
                <button className="button-secondary" onClick={() => saveToWishlist(product)} style={{ width: "100%", marginTop: "10px", padding: "10px", border: "1px solid #e7e9ee", boxShadow: "none" }}><Heart size={15}/> Save to wishlist</button>
                <button
                  className="button-secondary"
                  disabled={product.stock_quantity < 1}
                  onClick={() => buyNow(product)}
                  style={{ width: "100%", marginTop: "10px", padding: "10px", border: "1px solid #e7e9ee", boxShadow: "none", cursor: product.stock_quantity > 0 ? "pointer" : "not-allowed" }}
                >
                  {!user ? "Login to buy now" : "Buy now"}
                </button>
              </article>
            ))}
          </div>

          <aside style={{ background: "white", padding: "20px", borderRadius: "20px", boxShadow: "0 4px 8px -1px rgba(0,0,0,0.10)", position: "sticky", top: "24px" }}>
            <h2 style={{ marginTop: 0 }}>Your Cart</h2>
            {!user && <p>Login to add products to your cart and checkout.</p>}
            {user && !cartItems.length && <p>Your cart is empty.</p>}
            {cartItems.map((item) => (
              <div key={item.id} style={{ borderBottom: "1px solid #e2e8f0", padding: "12px 0" }}>
                <strong>{item.name}</strong>
                <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginTop: "8px" }}>
                  <div style={{ display: "flex", gap: "8px", alignItems: "center" }}>
                    <button onClick={() => updateCart(item, item.quantity - 1)} aria-label={`Remove one ${item.name}`}>−</button>
                    <span>{item.quantity}</span>
                    <button disabled={item.quantity >= item.stock_quantity} onClick={() => updateCart(item, item.quantity + 1)} aria-label={`Add one ${item.name}`}>+</button>
                  </div>
                  <span>${(item.price * item.quantity).toFixed(2)}</span>
                </div>
              </div>
            ))}
            <div style={{ display: "flex", justifyContent: "space-between", fontWeight: "bold", margin: "20px 0" }}>
              <span>Total</span><span>${cartTotal.toFixed(2)}</span>
            </div>
            {user && (
            <div style={{ borderTop: "1px solid #e2e8f0", paddingTop: "16px", marginTop: "16px" }}>
              <label htmlFor="coupon-code">Coupon code</label><input id="coupon-code" value={couponCode} onChange={(e) => setCouponCode(e.target.value.toUpperCase())} placeholder="Optional" style={{width:"100%",boxSizing:"border-box",marginBottom:"12px"}}/>
              <div style={{ display: "flex", alignItems: "center", gap: "8px", marginBottom: "12px" }}>
                <CreditCard size={18} aria-hidden="true" />
                <h3 style={{ margin: 0, fontSize: "16px" }}>Dummy Stripe Payment</h3>
              </div>
              <label htmlFor="stripe-cardholder">Cardholder name</label>
              <input
                id="stripe-cardholder"
                name="cardholder_name"
                value={payment.cardholder_name}
                onChange={handlePaymentChange}
                autoComplete="cc-name"
                style={{ marginBottom: "10px" }}
              />
              <label htmlFor="stripe-card-number">Card number</label>
              <input
                id="stripe-card-number"
                name="card_number"
                value={payment.card_number}
                onChange={handlePaymentChange}
                inputMode="numeric"
                autoComplete="cc-number"
                style={{ marginBottom: "10px" }}
              />
              <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: "10px" }}>
                <div>
                  <label htmlFor="stripe-expiry">Expiry</label>
                  <input
                    id="stripe-expiry"
                    name="expiry"
                    value={payment.expiry}
                    onChange={handlePaymentChange}
                    placeholder="MM/YY"
                    autoComplete="cc-exp"
                  />
                </div>
                <div>
                  <label htmlFor="stripe-cvc">CVC</label>
                  <input
                    id="stripe-cvc"
                    name="cvc"
                    value={payment.cvc}
                    onChange={handlePaymentChange}
                    inputMode="numeric"
                    autoComplete="cc-csc"
                  />
                </div>
              </div>
              <p style={{ display: "flex", alignItems: "center", gap: "6px", fontSize: "13px", margin: "12px 0 0" }}>
                <LockKeyhole size={14} aria-hidden="true" />
                Test card only. No real payment is processed.
              </p>
              {paymentStatus && <p style={{ color: "#166534", fontWeight: 700, marginBottom: 0 }}>{paymentStatus}</p>}
            </div>
            )}
            <button className="button-success" disabled={user ? !cartItems.length || submitting : false} onClick={checkout} style={{ width: "100%", padding: "12px", border: "none", fontWeight: "bold" }}>
              {!user ? "Login to checkout" : submitting ? "Processing payment..." : "Pay with Dummy Stripe"}
            </button>
          </aside>
        </div>
      ) : (
        <table style={{ width: "100%", background: "white", borderCollapse: "collapse" }}>
          <thead><tr><th>ID</th><th>Image</th><th>Name</th><th>SKU</th><th>Price</th><th>Stock</th><th>Vendor</th></tr></thead>
          <tbody>{products.map((product) => (
            <tr key={product.id}>
              <td>{product.id}</td>
              <td>
                <div style={{ width: "64px", height: "64px", overflow: "hidden", borderRadius: "12px", background: "#f5f5f5" }}>
                  {productImage(product)}
                </div>
              </td>
              <td>{product.name}</td>
              <td>{product.sku}</td>
              <td>${Number(product.price).toFixed(2)}</td>
              <td>{product.stock_quantity}</td>
              <td>{product.vendor_id}</td>
            </tr>
          ))}</tbody>
        </table>
      )}
    </div>
  );
}

export default Products;
