import PropTypes from "prop-types";
import React from "react";

function Pipes({ pipes }) {
  return pipes.map((pipe, ix) => (
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
}

export default Pipes;

Pipes.propTypes = {
  pipes: PropTypes.arrayOf(PropTypes.string),
};
