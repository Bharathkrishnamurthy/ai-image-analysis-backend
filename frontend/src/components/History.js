import React, { useEffect, useState } from "react";
import API from "../services/api";

const History = () => {
  const [data, setData] = useState([]);

  useEffect(() => {
    const fetchHistory = async () => {
      try {
        const res = await API.get("/image/history");

        console.log("API RESPONSE:", res.data);

        // 🔥 FIX: handle any backend structure
        const historyData =
          res.data?.data ||
          res.data?.results ||
          res.data?.history ||
          res.data;

        setData(Array.isArray(historyData) ? historyData : []);
      } catch (err) {
        console.error(err);
      }
    };

    fetchHistory();
  }, []);

  return (
    <div>
      <h2>📜 Upload History</h2>

      {data.length === 0 ? (
        <p>No history found</p>
      ) : (
        <div style={{ display: "grid", gap: "10px" }}>
          {data.map((item) => (
            <div
              key={item.request_id}
              style={{
                background: "#374151",
                padding: "10px",
                borderRadius: "8px",
              }}
            >
              <p><b>{item.filename}</b></p>
              <p>Status: {item.status}</p>
            </div>
          ))}
        </div>
      )}
    </div>
  );
};

export default History;