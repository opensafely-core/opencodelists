import React from "react";

const DescendantToggle = (props) => (
  <span
    onClick={props.toggleVisibility.bind(null, props.code)}
    style={{ cursor: "pointer", margin: "0 4px" }}
  >
    {props.isExpanded ? "⊟" : "⊞"}
  </span>
);

export default DescendantToggle;
