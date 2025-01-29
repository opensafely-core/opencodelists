import React from "react";
import Hierarchy from "../_hierarchy";
import { AncestorCode, PageData, ToggleVisibility } from "../types";
import TreeRow from "./TreeRow";

interface TreeProps {
  allCodes: PageData["allCodes"];
  ancestorCode: AncestorCode;
  codeToStatus: PageData["codeToStatus"];
  codeToTerm: PageData["codeToTerm"];
  hierarchy: Hierarchy;
  isEditable: PageData["isEditable"];
  toggleVisibility: ToggleVisibility;
  updateStatus: Function;
  visiblePaths: PageData["visiblePaths"];
}

export default function Tree({
  allCodes,
  ancestorCode,
  codeToStatus,
  codeToTerm,
  hierarchy,
  isEditable,
  toggleVisibility,
  updateStatus,
  visiblePaths,
}: TreeProps) {
  return hierarchy
    .treeRows(ancestorCode, codeToStatus, codeToTerm, visiblePaths)
    .map((row) => (
      <TreeRow
        allCodes={allCodes}
        code={row.code}
        codeToStatus={codeToStatus}
        codeToTerm={codeToTerm}
        hasDescendants={row.hasDescendants}
        hierarchy={hierarchy}
        isEditable={isEditable}
        isExpanded={row.isExpanded}
        key={row.path}
        path={row.path}
        pipes={row.pipes}
        status={row.status}
        term={row.term}
        toggleVisibility={toggleVisibility}
        updateStatus={updateStatus}
      />
    ));
}
