import React from "react";

function Filter({ filter }) {
  return filter ? (
    <p>Filtered to {filter} concepts and their descendants.</p>
  ) : null;
}

export default Filter;
