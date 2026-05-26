import React, { useEffect, useState } from "react";
import API from "../services/api";

const History = () => {
  const [data, setData] = useState([]);

  useEffect(() => {
    const fetchHistory = async () => {
      try {
        const res = await API.get("/image/history");
        setData(res.data);
      } catch (err) {
        console.error(err);
      }
    };

    fetchHistory();
  }, []);

  return (
    <div>
      <h2>📜 History</h2>

      {data.length === 0 ? (
        <p>No history found</p>
      ) : (
        data.map((item) => (
          <div
            key={item.request_id}
            style={{
              background: "#374151",
              padding: "10px",
              marginBottom: "10px",
              borderRadius: "8px",
            }}
          >
            <p><b>ID:</b> {item.request_id}</p>
            <p><b>Status:</b> {item.status}</p>
            <p><b>Created:</b> {item.created_at}</p>

            {item.results && (
              <pre>{JSON.stringify(item.results, null, 2)}</pre>
            )}
          </div>
        ))
      )}
    </div>
  );
};

export default History;