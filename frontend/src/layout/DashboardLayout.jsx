import { Link, Outlet } from "react-router-dom";
import Sidebar from "../components/Sidebar";
import { getStoredUser } from "../auth";

function DashboardLayout() {
  const user = getStoredUser();

  if (!user) {
    return (
      <div className="public-shell">
        <header className="storefront-header">
          <Link className="storefront-brand" to="/">
            <span className="storefront-brand-mark">B</span>
            <span>B2B Commerce</span>
          </Link>
          <Link className="storefront-login" to="/login">Login</Link>
        </header>

        <main className="public-main">
          <Outlet />
        </main>
      </div>
    );
  }

  return (
    <div className="app-shell">
      <Sidebar />

      <main className="main-content">
        <Outlet />
      </main>
    </div>
  );
}

export default DashboardLayout;
