import API from "./api";

// Upload Image
export const uploadImage = async (file) => {
  const formData = new FormData();
  formData.append("file", file);

  const res = await API.post("/image/predict", formData);
  return res.data;
};

// Get Result (for later use)
export const getResult = async (requestId) => {
  const res = await API.get(`/image/result/${requestId}`);
  return res.data;
};

// Get History
export const getHistory = async () => {
  const res = await API.get("/image/history");
  return res.data;
};