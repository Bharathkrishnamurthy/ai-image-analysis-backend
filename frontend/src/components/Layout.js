import React from "react";

const Layout = ({ children, active, setActive }) => {
  const handleLogout = () => {
    localStorage.removeItem("token");
    window.location.reload();
  };

  return (
    <div style={{ display: "flex", minHeight: "100vh" }}>
      
      {/* Sidebar */}
      <div style={{
        width: "230px",
        background: "#111827",
        color: "white",
        padding: "20px"
      }}>
        <h2>🚀 AI Dashboard</h2>

        <p
          onClick={() => setActive("upload")}
          style={{ cursor: "pointer", color: active === "upload" ? "#60a5fa" : "white" }}
        >
          Upload
        </p>

        <p
          onClick={() => setActive("analytics")}
          style={{ cursor: "pointer", color: active === "analytics" ? "#60a5fa" : "white" }}
        >
          Analytics
        </p>

        <p
          onClick={() => setActive("history")}
          style={{ cursor: "pointer", color: active === "history" ? "#60a5fa" : "white" }}
        >
          History
        </p>

        <br />
        <button onClick={handleLogout}>Logout</button>
      </div>

      {/* Main */}
      <div style={{
        flex: 1,
        padding: "20px",
        background: "#1f2937",
        color: "white"
      }}>
        {children}
      </div>
    </div>
  );
};

export default Layout;