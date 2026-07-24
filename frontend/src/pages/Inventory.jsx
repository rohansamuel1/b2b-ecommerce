import { useEffect, useState } from "react";
import API from "../api/api";

function Inventory() {
  const [inventory, setInventory] = useState([]);

  useEffect(() => {
    API.get("/inventory")
      .then((response) => setInventory(response.data))
      .catch((error) => console.error(error));
  }, []);

  const getStatus = (stock, reorder) => {
    if (stock === 0) return "Out of Stock";
    if (stock <= reorder) return "Low Stock";
    return "In Stock";
  };

  return (
    <div>
      <h1>Inventory</h1>

      <table
        style={{
          width: "100%",
          background: "white",
          marginTop: "20px",
          borderCollapse: "collapse",
        }}
      >
        <thead>
          <tr>
            <th>ID</th>
            <th>Product ID</th>
            <th>Stock</th>
            <th>Reorder Level</th>
            <th>Status</th>
          </tr>
        </thead>

        <tbody>
          {inventory.map((item) => (
            <tr key={item.id}>
              <td>{item.id}</td>
              <td>{item.product_id}</td>
              <td>{item.stock_quantity}</td>
              <td>{item.reorder_level}</td>
              <td><span className={`status-chip status-${getStatus(item.stock_quantity, item.reorder_level).toLowerCase().replaceAll(" ", "-")}`}>{getStatus(item.stock_quantity, item.reorder_level)}</span></td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

export default Inventory;
