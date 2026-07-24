import { BrowserRouter, Routes, Route, Navigate } from "react-router-dom";

import Login from "./pages/Login";
import DashboardLayout from "./layout/DashboardLayout";
import AdminDashboard from "./pages/AdminDashboard";
import Products from "./pages/Products";
import Inventory from "./pages/Inventory";
import Orders from "./pages/Orders";
import Vendors from "./pages/Vendors";
import AIAssistant from "./pages/AIAssistant";
import Analytics from "./pages/Analytics";
import PurchaseOrders from "./pages/PurchaseOrders";
import Recommendations from "./pages/Recommendations";
import KnowledgeBase from "./pages/KnowledgeBase";
import { getStoredUser } from "./auth";

function RequireAuth({ children }) {
  const token = localStorage.getItem("token");
  return token ? children : <Navigate to="/login" replace />;
}

function RequireRole({ roles, children }) {
  const user = getStoredUser();
  return user && roles.includes(user.role) ? children : <Navigate to="/login" replace />;
}

function App() {
  const token = localStorage.getItem("token");
  const user = getStoredUser();
  const isAdmin = user?.role === "admin";

  return (
    <BrowserRouter>
      <Routes>
        <Route
          path="/login"
          element={token ? <Navigate to="/" /> : <Login />}
        />

        <Route
          path="/"
          element={<DashboardLayout />}
        >
          <Route
            index
            element={isAdmin ? <AdminDashboard /> : <Products />}
          />
          <Route path="products" element={<Products />} />
          <Route path="orders" element={<RequireAuth><Orders /></RequireAuth>} />
          <Route path="assistant" element={<RequireAuth><AIAssistant /></RequireAuth>} />
          <Route path="recommendations" element={<RequireAuth><Recommendations /></RequireAuth>} />
          <Route path="knowledge" element={<RequireRole roles={["admin"]}><KnowledgeBase /></RequireRole>} />
          <Route path="inventory" element={<RequireRole roles={["admin"]}><Inventory /></RequireRole>} />
          <Route path="vendors" element={<RequireRole roles={["admin"]}><Vendors /></RequireRole>} />
          <Route path="analytics" element={<RequireRole roles={["admin"]}><Analytics /></RequireRole>} />
          <Route path="purchase-orders" element={<RequireRole roles={["admin"]}><PurchaseOrders /></RequireRole>} />
        </Route>
      </Routes>
    </BrowserRouter>
  );
}

export default App;
