import { useEffect, useState } from "react";
import API from "../api/api";

function PurchaseOrders() {
  const [purchaseOrders, setPurchaseOrders] = useState([]);

  const [form, setForm] = useState({
    vendor_id: "",
    product_id: "",
    quantity: "",
  });

  useEffect(() => {
    loadPurchaseOrders();
  }, []);

  async function loadPurchaseOrders() {
    const response = await API.get("/purchase-orders");
    setPurchaseOrders(response.data);
  }

  const handleChange = (e) => {
    setForm({
      ...form,
      [e.target.name]: e.target.value,
    });
  };

  const createPurchaseOrder = async (e) => {
    e.preventDefault();

    await API.post("/purchase-orders", {
      vendor_id: Number(form.vendor_id),
      items: [
        {
          product_id: Number(form.product_id),
          quantity: Number(form.quantity),
        },
      ],
    });

    setForm({
      vendor_id: "",
      product_id: "",
      quantity: "",
    });

    loadPurchaseOrders();
  };

  const markReceived = async (id) => {
    await API.put(`/purchase-orders/${id}/status`, {
      status: "RECEIVED",
    });

    loadPurchaseOrders();
  };

  return (
    <div>
      <h1>Purchase Orders</h1>

      <form
        onSubmit={createPurchaseOrder}
        style={{
          background: "white",
          padding: "20px",
          borderRadius: "12px",
          marginTop: "20px",
          marginBottom: "24px",
          display: "grid",
          gridTemplateColumns: "repeat(4, 1fr)",
          gap: "12px",
          boxShadow: "0 2px 10px rgba(0,0,0,0.08)",
        }}
      >
        <input
          name="vendor_id"
          placeholder="Vendor ID"
          value={form.vendor_id}
          onChange={handleChange}
        />

        <input
          name="product_id"
          placeholder="Product ID"
          value={form.product_id}
          onChange={handleChange}
        />

        <input
          name="quantity"
          placeholder="Quantity"
          value={form.quantity}
          onChange={handleChange}
        />

        <button
          type="submit"
          style={{
            background: "#2563eb",
            color: "white",
            border: "none",
            borderRadius: "8px",
          }}
        >
          Create PO
        </button>
      </form>

      <table
        style={{
          width: "100%",
          background: "white",
          borderCollapse: "collapse",
        }}
      >
        <thead>
          <tr>
            <th>PO ID</th>
            <th>Vendor ID</th>
            <th>Status</th>
            <th>Total</th>
            <th>Created</th>
            <th>Received</th>
            <th>Action</th>
          </tr>
        </thead>

        <tbody>
          {purchaseOrders.map((po) => (
            <tr key={po.id}>
              <td>{po.id}</td>
              <td>{po.vendor_id}</td>
              <td><span className={`status-chip status-${po.status.toLowerCase()}`}>{po.status}</span></td>
              <td>${po.total_amount}</td>
              <td>{new Date(po.created_at).toLocaleString()}</td>
              <td>
                {po.received_at
                  ? new Date(po.received_at).toLocaleString()
                  : "Not received"}
              </td>
              <td>
                {po.status !== "RECEIVED" && (
                  <button
                    className="button-success"
                    onClick={() => markReceived(po.id)}
                    style={{
                      background: "#16a34a",
                      color: "white",
                      border: "none",
                      padding: "8px 12px",
                      borderRadius: "6px",
                    }}
                  >
                    Mark Received
                  </button>
                )}
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

export default PurchaseOrders;
