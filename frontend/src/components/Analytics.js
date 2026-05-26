import React, { useEffect, useState } from "react";
import API from "../services/api";
import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  Tooltip,
  ResponsiveContainer,
  PieChart,
  Pie,
  Cell,
} from "recharts";

const Analytics = () => {
  const [data, setData] = useState([]);

  useEffect(() => {
    const fetchData = async () => {
      try {
        const res = await API.get("/image/history");

        const history = res.data;

        const success = history.filter((i) => i.status === "completed").length;
        const failed = history.filter((i) => i.status === "failed").length;

        setData([
          { name: "Success", value: success },
          { name: "Failed", value: failed },
        ]);
      } catch (err) {
        console.error(err);
      }
    };

    fetchData();
  }, []);

  const COLORS = ["#22c55e", "#ef4444"];

  return (
    <div>
      <h2>📊 Analytics Dashboard</h2>

      <div style={{ display: "flex", gap: "30px", marginTop: "20px" }}>
        
        {/* Bar Chart */}
        <div style={{ width: "50%", height: 300 }}>
          <ResponsiveContainer>
            <BarChart data={data}>
              <XAxis dataKey="name" stroke="#fff" />
              <YAxis stroke="#fff" />
              <Tooltip />
              <Bar dataKey="value" />
            </BarChart>
          </ResponsiveContainer>
        </div>

        {/* Pie Chart */}
        <div style={{ width: "50%", height: 300 }}>
          <ResponsiveContainer>
            <PieChart>
              <Pie
                data={data}
                dataKey="value"
                outerRadius={100}
                label
              >
                {data.map((entry, index) => (
                  <Cell key={index} fill={COLORS[index]} />
                ))}
              </Pie>
              <Tooltip />
            </PieChart>
          </ResponsiveContainer>
        </div>

      </div>
    </div>
  );
};

export default Analytics;