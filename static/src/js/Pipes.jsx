import React from "react";

const Pipes = (props) =>
  props.pipes.map((pipe, ix) => (
    <span
      key={ix}
      style={{
        display: "inline-block",
        textAlign: "center",
        paddingLeft: "3px",
        paddingRight: "6px",
        width: "20px",
      }}
    >
      {pipe}
    </span>
  ));

export default Pipes;
