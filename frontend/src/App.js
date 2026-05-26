import React, { useState } from "react";
import Layout from "./components/Layout";

import Upload from "./components/Upload";
import Analytics from "./components/Analytics";
import History from "./components/History";
import Login from "./components/Login";

function App() {
  const [active, setActive] = useState("upload");

  const token = localStorage.getItem("token");

  // 🔐 If not logged in → show login page
  if (!token) {
    return <Login />;
  }

  const renderPage = () => {
    switch (active) {
      case "upload":
        return <Upload />;
      case "analytics":
        return <Analytics />;
      case "history":
        return <History />;
      default:
        return <Upload />;
    }
  };

  return (
    <Layout active={active} setActive={setActive}>
      {renderPage()}
    </Layout>
  );
}

export default App;