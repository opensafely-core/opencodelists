import React from "react";

export interface FilterProps {
  filter?: string;
}

export default function Filter({ filter }: FilterProps) {
  return filter ? (
    <p>Filtered to {filter} concepts and their descendants.</p>
  ) : (
    ""
  );
}
