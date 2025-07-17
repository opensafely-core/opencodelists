import React from "react";
import { useCodelistContext } from "../../context/codelist-context";
import { AncestorCode, PageData, ToggleVisibility } from "../../types";
import Row from "./Row";

interface TreeProps {
  ancestorCode: AncestorCode;
  toggleVisibility: ToggleVisibility;
  updateStatus: Function;
  visiblePaths: PageData["visiblePaths"];
}

export default function Tree({
  ancestorCode,
  toggleVisibility,
  updateStatus,
  visiblePaths,
}: TreeProps) {
  const { codeToStatus, codeToTerm, hierarchy, sortByTerm } =
    useCodelistContext();

  return hierarchy
    .treeRows(ancestorCode, codeToStatus, codeToTerm, visiblePaths, sortByTerm)
    .map((row) => (
      <Row
        code={row.code}
        hasDescendants={row.hasDescendants}
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
