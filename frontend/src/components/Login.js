import React, { useState } from "react";
import { loginUser, registerUser } from "../services/authService";

const Login = () => {
  const [isLogin, setIsLogin] = useState(true);
  const [username, setUsername] = useState("");
  const [password, setPassword] = useState("");

  const handleSubmit = async () => {
    console.log("🔥 Button clicked");

    if (!username || !password) {
      return alert("Enter username & password");
    }

    try {
      if (isLogin) {
        const data = await loginUser(username, password);

        console.log("LOGIN RESPONSE:", data);

        localStorage.setItem("token", data.access_token);

        alert("Login success 🚀");
        window.location.reload();
      } else {
        const data = await registerUser(username, password);

        console.log("REGISTER RESPONSE:", data);

        alert("Signup success ✅");
        setIsLogin(true);
      }
    } catch (err) {
      console.error("ERROR:", err?.response?.data || err.message);
      alert("Error ❌ Check console");
    }
  };

  return (
    <div style={{ textAlign: "center", marginTop: "100px" }}>
      <h2>{isLogin ? "Login" : "Signup"}</h2>

      <input
        placeholder="Username"
        onChange={(e) => setUsername(e.target.value)}
      />

      <br />

      <input
        type="password"
        placeholder="Password"
        onChange={(e) => setPassword(e.target.value)}
      />

      <br /><br />

      <button onClick={handleSubmit}>
        {isLogin ? "Login" : "Sign Up"}
      </button>

      <br /><br />

      <p
        onClick={() => setIsLogin(!isLogin)}
        style={{ cursor: "pointer", color: "blue" }}
      >
        {isLogin ? "New user? Signup" : "Already have account? Login"}
      </p>
    </div>
  );
};

export default Login;