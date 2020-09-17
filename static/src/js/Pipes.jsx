import React from "react";

const Pipes = (props) =>
  props.pipes.map((pipe, ix) => (
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
  ));

export default Pipes;
