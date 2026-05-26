
import React from "react";

const Loader = () => {
  return (
    <div style={{ textAlign: "center", marginTop: "20px" }}>
      <div className="spinner"></div>

      <style>{`
        .spinner {
          border: 4px solid #ccc;
          border-top: 4px solid #3b82f6;
          border-radius: 50%;
          width: 40px;
          height: 40px;
          animation: spin 1s linear infinite;
          margin: auto;
        }

        @keyframes spin {
          0% { transform: rotate(0deg); }
          100% { transform: rotate(360deg); }
        }
      `}</style>
    </div>
  );
};

export default Loader;