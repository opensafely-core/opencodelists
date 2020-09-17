import React from "react";

export default function TermAndCode(props) {
  const {
    term,
    code,
    pipes,
    status,
    hasDescendants,
    isExpanded,
    toggleVisibility,
  } = props;

  const termStyle = {
    color: {
      "!": "red",
      "-": "gray",
      "(-)": "gray",
    }[status],
  };

  return (
    <div style={{ paddingLeft: "10px", whiteSpace: "nowrap" }}>
      {pipes.map((pipe, ix) => (
        <span
          key={ix}
          style={{
            display: "inline-block",
            textAlign: "center",
            width: "20px",
          }}
        >
          {pipe}
        </span>
      ))}
      {hasDescendants ? (
        <span
          onClick={toggleVisibility.bind(null, code)}
          style={{ cursor: "pointer", margin: "0 4px" }}
        >
          {isExpanded ? "⊟" : "⊞"}
        </span>
      ) : null}
      <span style={termStyle}>{term}</span>{" "}
      <span>
        (<code>{code}</code>)
      </span>
    </div>
  );
}
