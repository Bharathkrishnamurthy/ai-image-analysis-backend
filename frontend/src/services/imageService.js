import API from "./api";

// 🚀 Upload Image
export const uploadImage = async (file) => {
  const formData = new FormData();
  formData.append("file", file);

  const res = await API.post("/image/predict", formData, {
    headers: {
      "Content-Type": "multipart/form-data",
    },
  });

  return res.data;
};

// 📊 Get Result
export const getResult = async (requestId) => {
  const res = await API.get(`/image/result/${requestId}`);
  return res.data;
};

// 📜 Get History
export const getHistory = async () => {
  const res = await API.get("/image/history");
  return res.data;
};