import React from "react";
import type Hierarchy from "../../_hierarchy";
import type { AncestorCodes, PageData, ToggleVisibility } from "../../types";
import Tree from "./Tree";

interface SectionProps {
  allCodes: PageData["allCodes"];
  ancestorCodes: AncestorCodes;
  codeToStatus: PageData["codeToStatus"];
  codeToTerm: PageData["codeToTerm"];
  heading: string;
  hierarchy: Hierarchy;
  isEditable: PageData["isEditable"];
  toggleVisibility: ToggleVisibility;
  updateStatus: Function;
  visiblePaths: PageData["visiblePaths"];
}

export default function Section({
  allCodes,
  ancestorCodes,
  codeToStatus,
  codeToTerm,
  heading,
  hierarchy,
  isEditable,
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
            allCodes={allCodes}
            ancestorCode={ancestorCode}
            codeToStatus={codeToStatus}
            codeToTerm={codeToTerm}
            hierarchy={hierarchy}
            isEditable={isEditable}
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
