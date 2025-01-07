import PropTypes from "prop-types";
import React from "react";

function Filter({ filter }) {
  return filter ? (
    <p>Filtered to {filter} concepts and their descendants.</p>
  ) : (
    ""
  );
}

export default Filter;

Filter.propTypes = {
  filter: PropTypes.string,
};
