import { useEffect, useState } from "react";
import API from "../api/api";
import StatCard from "../components/StatCard";

function AdminDashboard() {
  const [stats, setStats] = useState(null);

  useEffect(() => {
    API.get("/dashboard/admin")
      .then((response) => setStats(response.data))
      .catch((error) => console.error(error));
  }, []);

  if (!stats) {
    return <h2>Loading Dashboard...</h2>;
  }

  return (
    <div>
      <span className="eyebrow">Operations overview</span>
      <h1>Admin Dashboard</h1>
      <p>Monitor commerce activity, fulfillment, and supply health.</p>

      <div className="stats-grid">
        <StatCard
          title="Users"
          value={stats.total_users}
        />

        <StatCard
          title="Vendors"
          value={stats.total_vendors}
        />

        <StatCard
          title="Products"
          value={stats.total_products}
        />

        <StatCard
          title="Orders"
          value={stats.total_orders}
        />

        <StatCard
          title="Revenue"
          value={`$${stats.total_revenue}`}
        />

        <StatCard
          title="Low Stock"
          value={stats.low_stock_alerts}
        />
      </div>
    </div>
  );
}

export default AdminDashboard;
