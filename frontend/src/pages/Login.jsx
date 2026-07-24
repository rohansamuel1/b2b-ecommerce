import { useState } from "react";
import { Boxes } from "lucide-react";
import { useNavigate } from "react-router-dom";
import API from "../api/api";

function Login() {
  const navigate = useNavigate();
  const [email, setEmail] = useState("rohan@test.com");
  const [password, setPassword] = useState("123456");
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);

  const handleLogin = async (event) => {
    event.preventDefault();
    setLoading(true);
    setError("");
    try {
      const formData = new FormData();
      formData.append("username", email);
      formData.append("password", password);
      const response = await API.post("/auth/login", formData);
      localStorage.setItem("token", response.data.access_token);
      localStorage.setItem("user", JSON.stringify(response.data.user));
      navigate("/");
      window.location.reload();
    } catch (requestError) {
      setError(requestError.response?.data?.detail || "Unable to sign in");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="login-page">
      <section className="login-brand-panel">
        <div className="brand" style={{ border: 0, padding: 0 }}>
          <div className="brand-mark"><Boxes size={20} /></div>
          <div><div className="brand-name">Rohan's Demo B2B</div><div className="brand-caption">Demo Business Operations</div></div>
        </div>
        <div><span className="eyebrow" style={{ color: "#b7c8de" }}>Supply chain workspace</span><h1 style={{ fontSize: "32px", lineHeight: "40px" }}>A Demo Platform for Shopping</h1><p>Manage purchasing, inventory, vendors, orders, and fulfillment from this workspace.</p></div>
        <small style={{ color: "#b7c8de" }}>Secure role-based access</small>
      </section>
      <main className="login-content">
        <form className="login-form" onSubmit={handleLogin}>
          <span className="eyebrow">Account access</span>
          <h1>Sign in</h1>
          <p>Enter your credentials to continue.</p>
          {error && <p className="error-banner">{error}</p>}
          <div className="field"><label htmlFor="email">Email address</label><input id="email" type="email" required value={email} onChange={(event) => setEmail(event.target.value)} autoComplete="email" /></div>
          <div className="field"><label htmlFor="password">Password</label><input id="password" type="password" required value={password} onChange={(event) => setPassword(event.target.value)} autoComplete="current-password" /></div>
          <button type="submit" disabled={loading}>{loading ? "Signing in..." : "Sign in"}</button>
        </form>
      </main>
    </div>
  );
}

export default Login;
