import React from "react";

export interface FilterProps {
  filter: string;
}

function Filter({ filter }: FilterProps) {
  return filter ? (
    <p>Filtered to {filter} concepts and their descendants.</p>
  ) : (
    ""
  );
}

export default Filter;
