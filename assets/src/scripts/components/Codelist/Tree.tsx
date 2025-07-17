import React, { useContext } from "react";
import { readValueFromPage } from "../../_utils";
import { AncestorCode, PageData, ToggleVisibility } from "../../types";
import { CodelistContext } from "../Layout/CodelistTab";
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
  const { codeToStatus, codeToTerm, hierarchy } = useContext(CodelistContext);
  const sortByTerm: PageData["sortByTerm"] = readValueFromPage("sort-by-term");

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
