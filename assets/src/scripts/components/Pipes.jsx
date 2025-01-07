import PropTypes from "prop-types";
import React from "react";

function Pipes({ pipes }) {
  return pipes.map((pipe, ix) => (
    <span
      key={ix}
      className="d-inline-block pl-1 pr-2 text-center text-monospace"
    >
      {pipe}
    </span>
  ));
}

export default Pipes;

Pipes.propTypes = {
  pipes: PropTypes.arrayOf(PropTypes.string),
};
