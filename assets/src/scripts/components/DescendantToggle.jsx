import React from "react";

function DescendantToggle({ isExpanded, path, toggleVisibility }) {
  return (
    <span
      onClick={toggleVisibility.bind(null, path)}
      style={{ cursor: "pointer", marginLeft: "2px", marginRight: "4px" }}
    >
      {" "}
      {isExpanded ? "⊟" : "⊞"}
    </span>
  );
}

export default DescendantToggle;
