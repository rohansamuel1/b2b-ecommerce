import { NavLink, useNavigate } from "react-router-dom";
import {
  Bot, Boxes, Building2, ChartNoAxesCombined, ClipboardList, BookOpen, Sparkles,
  LayoutDashboard, LogOut, PackageSearch, ShoppingCart, Warehouse,
} from "lucide-react";
import { clearSession, getStoredUser } from "../auth";

function Sidebar() {
  const navigate = useNavigate();
  const user = getStoredUser();
  const isAdmin = user?.role === "admin";
  const initial = user?.name?.trim()?.[0]?.toUpperCase() || "U";

  const links = isAdmin
    ? [
        ["/", "Dashboard", LayoutDashboard, true],
        ["/products", "Products", PackageSearch],
        ["/orders", "Orders", ClipboardList],
        ["/inventory", "Inventory", Warehouse],
        ["/vendors", "Vendors", Building2],
        ["/purchase-orders", "Purchase Orders", Boxes],
        ["/analytics", "Analytics", ChartNoAxesCombined],
        ["/assistant", "AI Assistant", Bot],
        ["/recommendations", "Recommendations", Sparkles],
        ["/knowledge", "Knowledge Base", BookOpen],
      ]
    : [
        ["/products", "Shop", ShoppingCart],
        ["/orders", "My Orders", ClipboardList],
        ["/assistant", "AI Assistant", Bot],
        ["/recommendations", "For You", Sparkles],
      ];

  const logout = () => {
    clearSession();
    navigate("/login");
    window.location.reload();
  };

  return (
    <aside className="sidebar">
      <div className="brand">
        <div className="brand-mark"><Boxes size={18} /></div>
        <div><div className="brand-name">B2B Commerce</div><div className="brand-caption">Operations Console</div></div>
      </div>

      <div className="user-panel">
        <div className="user-avatar">{initial}</div>
        <div style={{ minWidth: 0 }}><div className="user-name">{user?.name}</div><div className="user-role">{user?.role}</div></div>
      </div>

      <nav className="sidebar-nav">
        {links.map(([to, label, Icon, end]) => (
          <NavLink key={to} to={to} end={end}>
            <Icon size={17} strokeWidth={1.8} /> {label}
          </NavLink>
        ))}
      </nav>

      <button className="logout-button" onClick={logout}><LogOut size={16} /><span>Sign out</span></button>
    </aside>
  );
}

export default Sidebar;
