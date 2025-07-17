import React from "react";
import Hierarchy from "../../_hierarchy";
import { AncestorCodes, PageData, ToggleVisibility } from "../../types";
import Tree from "./Tree";

interface SectionProps {
  ancestorCodes: AncestorCodes;
  heading: string;
  hierarchy: Hierarchy;
  toggleVisibility: ToggleVisibility;
  updateStatus: Function;
  visiblePaths: PageData["visiblePaths"];
}

export default function Section({
  ancestorCodes,
  heading,
  toggleVisibility,
  updateStatus,
  visiblePaths,
}: SectionProps) {
  return (
    <div className="mb-2 pb-2 overflow-auto">
      <h5>{heading}</h5>
      <div className="builder__container">
        {ancestorCodes.map((ancestorCode) => (
          <Tree
            ancestorCode={ancestorCode}
            key={ancestorCode}
            toggleVisibility={toggleVisibility}
            updateStatus={updateStatus}
            visiblePaths={visiblePaths}
          />
        ))}
      </div>
    </div>
  );
}
