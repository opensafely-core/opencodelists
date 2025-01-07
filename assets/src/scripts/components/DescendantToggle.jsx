import PropTypes from "prop-types";
import React from "react";

function DescendantToggle({ isExpanded, path, toggleVisibility }) {
  return (
    <button
      className="p-0 bg-white border-0 text-monospace d-inline-block ml-1 mr-2"
      onClick={toggleVisibility.bind(null, path)}
      type="button"
    >
      {" "}
      {isExpanded ? "⊟" : "⊞"}
    </button>
  );
}

export default DescendantToggle;

DescendantToggle.propTypes = {
  isExpanded: PropTypes.bool,
  path: PropTypes.string,
  toggleVisibility: PropTypes.func,
};
