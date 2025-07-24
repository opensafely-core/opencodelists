import React from "react";
import type { IsExpanded, Path, ToggleVisibility } from "../../types";

interface DescendantToggleProps {
  isExpanded: IsExpanded;
  path: Path;
  toggleVisibility: ToggleVisibility;
}

export default function DescendantToggle({
  isExpanded,
  path,
  toggleVisibility,
}: DescendantToggleProps) {
  return (
    <button
      className="p-0 bg-transparent border-0 text-monospace d-inline-block ml-1 mr-2"
      onClick={toggleVisibility.bind(null, path)}
      type="button"
    >
      {" "}
      {isExpanded ? "⊟" : "⊞"}
    </button>
  );
}
