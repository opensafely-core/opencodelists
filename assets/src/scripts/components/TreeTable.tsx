import React from "react";
import Hierarchy from "../_hierarchy";
import { AncestorCodes, PageData, ToggleVisibility } from "../types";
import Tree from "./Tree";

interface TreeTableProps {
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

export default function TreeTable({
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
}: TreeTableProps) {
  return (
    <div className="mb-4 overflow-auto">
      <h5>{heading}</h5>

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
  );
}
