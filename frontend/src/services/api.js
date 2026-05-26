import axios from "axios";

const API = axios.create({
  baseURL: "http://localhost:8000", // 🔥 CHANGE THIS FOR LOCAL TEST
});

// 🔐 Attach token
API.interceptors.request.use((config) => {
  const token = localStorage.getItem("token");

  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }

  return config;
});

// ❌ Error debug
API.interceptors.response.use(
  (res) => res,
  (err) => {
    console.error("API ERROR:", err?.response?.data || err.message);
    return Promise.reject(err);
  }
);

export default API;