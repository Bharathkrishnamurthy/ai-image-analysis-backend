import React, { useState } from "react";
import API from "../services/api";

const Upload = () => {
  const [file, setFile] = useState(null);

  const handleUpload = async () => {
    console.log("UPLOAD CLICKED");

    if (!file) return alert("Select a file");

    const formData = new FormData();
    formData.append("file", file);

    try {
      const res = await API.post("/image/predict", formData);

      console.log(res.data);
      alert("Upload success 🚀");
    } catch (err) {
      console.error(err.response?.data || err.message);
      alert("Upload failed ❌");
    }
  };

  return (
    <div>
      <input type="file" onChange={(e) => setFile(e.target.files[0])} />
      <button onClick={handleUpload}>Upload</button>
    </div>
  );
};

export default Upload;