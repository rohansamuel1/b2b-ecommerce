import { useEffect, useState } from "react";
import { Link, useSearchParams } from "react-router-dom";
import API from "../api/api";
import { getStoredUser } from "../auth";

function Orders() {
  const user = getStoredUser();
  const isAdmin = user?.role === "admin";
  const [searchParams] = useSearchParams();
  const [orders, setOrders] = useState([]);
  const [invoice, setInvoice] = useState(null);
  const [loading, setLoading] = useState(true);
  const [shipment, setShipment] = useState(null);
  const [returnReason, setReturnReason] = useState("");
  const [selectedOrder, setSelectedOrder] = useState(null);

  useEffect(() => {
    loadOrders();
  }, []);

  async function loadOrders() {
    try {
      setLoading(true);
      const response = await API.get("/orders");
      setOrders(response.data);
    } catch (error) {
      console.error("Failed to load orders:", error);
    } finally {
      setLoading(false);
    }
  }

  const viewInvoice = async (orderId) => {
    try {
      const response = await API.get(`/invoices/order/${orderId}`);
      setInvoice(response.data);
    } catch (error) {
      console.error(error);
    }
  };

  const trackOrder = async (orderId) => {
    const response = await API.get(`/orders/${orderId}/shipment`);
    setShipment(response.data); setSelectedOrder(orderId);
  };

  const requestReturn = async () => {
    if (!selectedOrder || returnReason.trim().length < 5) return;
    await API.post(`/orders/${selectedOrder}/returns`, { reason: returnReason });
    setReturnReason(""); setShipment({ ...shipment, return_requested: true });
  };

  return (
    <div>

      <div
        style={{
          display: "flex",
          justifyContent: "space-between",
          alignItems: "center",
          marginBottom: "20px",
        }}
      >
        <h1>{isAdmin ? "Orders" : "My Orders"}</h1>

        <button
          onClick={loadOrders}
          style={{
            background: "#2563eb",
            color: "white",
            border: "none",
            padding: "10px 18px",
            borderRadius: "8px",
            cursor: "pointer",
          }}
        >
          Refresh
        </button>
      </div>

      {searchParams.get("placed") && (
        <p style={{ color: "#166534", background: "#f0fdf4", padding: "12px", borderRadius: "8px" }}>
          Order #{searchParams.get("placed")} was placed successfully.
        </p>
      )}

      {loading ? (
        <h3>Loading Orders...</h3>
      ) : orders.length === 0 ? (
        <div style={{ background: "white", padding: "32px", borderRadius: "12px", textAlign: "center" }}>
          <h3>No orders yet</h3>
          <p style={{ color: "#64748b" }}>Products you purchase will appear here.</p>
          {!isAdmin && <Link to="/products">Shop products</Link>}
        </div>
      ) : (
        <table
          style={{
            width: "100%",
            background: "white",
            borderCollapse: "collapse",
            borderRadius: "12px",
            overflow: "hidden",
            boxShadow: "0 2px 12px rgba(0,0,0,0.08)",
          }}
        >
          <thead
            style={{
              background: "#0f172a",
              color: "white",
            }}
          >
            <tr>
              <th style={{ padding: "14px" }}>Order ID</th>
              {isAdmin && <th>Buyer</th>}
              <th>Status</th>
              <th>Total</th>
              <th>Created</th>
              <th>Invoice</th>
              <th>Support</th>
            </tr>
          </thead>

          <tbody>
            {orders.map((order) => (
              <tr
                key={order.id}
                style={{
                  borderBottom: "1px solid #e2e8f0",
                }}
              >
                <td style={{ padding: "12px" }}>{order.id}</td>

                {isAdmin && <td>{order.buyer_id}</td>}

                <td>
                  <span className={`status-chip status-${order.status.toLowerCase()}`}>
                    {order.status}
                  </span>
                </td>
                <td><button className="button-secondary" onClick={() => trackOrder(order.id)} style={{padding:"8px 12px"}}>Track / Return</button></td>

                <td>${order.total_amount.toFixed(2)}</td>

                <td>
                  {new Date(order.created_at).toLocaleString()}
                </td>

                <td>
                  <button
                    onClick={() => viewInvoice(order.id)}
                    style={{
                      background: "#2563eb",
                      color: "white",
                      border: "none",
                      padding: "8px 14px",
                      borderRadius: "8px",
                      cursor: "pointer",
                    }}
                  >
                    View Invoice
                  </button>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      )}

      {shipment && <section className="shipment-panel"><h2>Order #{selectedOrder} support</h2><div className="shipment-grid"><p><b>Shipment:</b> {shipment.status}</p><p><b>Carrier:</b> {shipment.carrier || "Not assigned"}</p><p><b>Tracking:</b> {shipment.tracking_number || "Not assigned"}</p><p><b>Estimated delivery:</b> {shipment.estimated_delivery ? new Date(shipment.estimated_delivery).toLocaleString() : "Pending"}</p></div><p>{shipment.last_event}</p>{shipment.return_requested ? <p className="notice">Return request submitted.</p> : <div className="return-form"><input value={returnReason} onChange={e=>setReturnReason(e.target.value)} placeholder="Reason for return (at least 5 characters)"/><button onClick={requestReturn}>Request return</button></div>}</section>}

      {invoice && (
        <div
          style={{
            marginTop: "40px",
            background: "white",
            padding: "30px",
            borderRadius: "16px",
            boxShadow: "0 4px 20px rgba(0,0,0,0.08)",
          }}
        >
          <div
            style={{
              display: "flex",
              justifyContent: "space-between",
            }}
          >
            <div>
              <h2>{invoice.invoice_number}</h2>

              <p>
                <strong>Order:</strong> {invoice.order_id}
              </p>

              <p>
                <strong>Buyer:</strong> {invoice.buyer_id}
              </p>

              <p>
                <strong>Status:</strong> {invoice.status}
              </p>

              <p>
                <strong>Total:</strong> $
                {invoice.total_amount.toFixed(2)}
              </p>
            </div>

            <button
              onClick={() => window.print()}
              style={{
                height: "45px",
                background: "#16a34a",
                color: "white",
                border: "none",
                borderRadius: "8px",
                padding: "0 20px",
                cursor: "pointer",
              }}
            >
              🖨 Print Invoice
            </button>
          </div>

          <h3 style={{ marginTop: "30px" }}>
            Invoice Items
          </h3>

          <table
            style={{
              width: "100%",
              borderCollapse: "collapse",
            }}
          >
            <thead
              style={{
                background: "#f8fafc",
              }}
            >
              <tr>
                <th style={{ padding: "12px" }}>Product</th>
                <th>Vendor</th>
                <th>Qty</th>
                <th>Unit Price</th>
                <th>Subtotal</th>
              </tr>
            </thead>

            <tbody>
              {invoice.items.map((item, index) => (
                <tr
                  key={index}
                  style={{
                    borderBottom: "1px solid #e2e8f0",
                  }}
                >
                  <td style={{ padding: "12px" }}>
                    {item.product_name}
                  </td>

                  <td>{item.vendor_id}</td>

                  <td>{item.quantity}</td>

                  <td>${item.unit_price.toFixed(2)}</td>

                  <td>${item.subtotal.toFixed(2)}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}

export default Orders;
