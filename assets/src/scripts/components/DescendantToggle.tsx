import React from "react";

interface DescendantToggleProps {
  isExpanded: boolean;
  path: string;
  toggleVisibility: Function;
}

function DescendantToggle({
  isExpanded,
  path,
  toggleVisibility,
}: DescendantToggleProps) {
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
