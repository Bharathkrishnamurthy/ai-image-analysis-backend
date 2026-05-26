
import React from "react";

const Result = ({ result }) => {
  if (!result) return null;

  return (
    <div style={{ marginTop: "20px" }}>
      <h2>Detection Result</h2>

      <div style={{ position: "relative", display: "inline-block" }}>
        <img src={result.image_url} alt="result" width="400" />

        {result.result.detections?.map((obj, i) => (
          <div
            key={i}
            style={{
              position: "absolute",
              border: "2px solid red",
              left: obj.bbox.x1,
              top: obj.bbox.y1,
              width: obj.bbox.x2 - obj.bbox.x1,
              height: obj.bbox.y2 - obj.bbox.y1,
              color: "white",
              fontSize: "12px"
            }}
          >
            {obj.label}
          </div>
        ))}
      </div>
    </div>
  );
};

export default Result;