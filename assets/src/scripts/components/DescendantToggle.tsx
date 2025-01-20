import React from "react";

interface DescendantToggleProps {
  isExpanded: boolean;
  path: string;
  toggleVisibility: (path: string) => void;
}

export default function DescendantToggle({
  isExpanded,
  path,
  toggleVisibility,
}: DescendantToggleProps) {
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
