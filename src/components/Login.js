import React, { useState } from "react";
import { loginUser } from "../services/authService";

const Login = ({ setToken }) => {
  const [username, setUsername] = useState("");
  const [password, setPassword] = useState("");

  const handleLogin = async () => {
    try {
      const data = await loginUser(username, password);
      const token = data.access_token;

      localStorage.setItem("token", token);
      setToken(token);

      alert("Login successful 🚀");
    } catch (err) {
      console.error(err);
      alert("Login failed");
    }
  };

  return (
    <div style={{ marginBottom: "20px" }}>
      <input
        placeholder="Username"
        onChange={(e) => setUsername(e.target.value)}
      />
      <input
        type="password"
        placeholder="Password"
        onChange={(e) => setPassword(e.target.value)}
      />
      <button onClick={handleLogin}>Login</button>
    </div>
  );
};

export default Login;