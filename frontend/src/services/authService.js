import API from "./api";

// 🔐 LOGIN
export const loginUser = async (username, password) => {
  const params = new URLSearchParams();

  params.append("username", username);
  params.append("password", password);
  params.append("grant_type", "password");

  const res = await API.post("/auth/login", params, {
    headers: {
      "Content-Type": "application/x-www-form-urlencoded",
    },
  });

  return res.data;
};

// 🆕 REGISTER
export const registerUser = async (username, password) => {
  const res = await API.post("/auth/register", {
    username,
    password,
  });

  return res.data;
};