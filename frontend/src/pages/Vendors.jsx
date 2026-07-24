import { useEffect, useState } from "react";
import API from "../api/api";

function Vendors() {
  const [vendors, setVendors] = useState([]);

  useEffect(() => {
    API.get("/vendors")
      .then((response) => setVendors(response.data))
      .catch((error) => console.error(error));
  }, []);

  return (
    <div>
      <h1>Vendors</h1>

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
            <th>Company</th>
            <th>Email</th>
            <th>Phone</th>
            <th>User ID</th>
          </tr>
        </thead>

        <tbody>
          {vendors.map((vendor) => (
            <tr key={vendor.id}>
              <td>{vendor.id}</td>
              <td>{vendor.company_name}</td>
              <td>{vendor.contact_email}</td>
              <td>{vendor.phone}</td>
              <td>{vendor.user_id}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

export default Vendors;
