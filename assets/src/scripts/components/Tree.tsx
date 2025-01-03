import React from "react";
import Hierarchy from "../_hierarchy";
import { CodeToStatus } from "../types";
import TreeRow from "./TreeRow";

export interface TreeProps {
  ancestorCode: string;
  codeToStatus: CodeToStatus;
  codeToTerm: {
    [key: string]: string;
  };
  hierarchy: Hierarchy;
  showMoreInfoModal: Function;
  toggleVisibility: Function;
  updateStatus: Function;
  visiblePaths: Set<string>;
}

function Tree({
  ancestorCode,
  codeToStatus,
  codeToTerm,
  hierarchy,
  showMoreInfoModal,
  toggleVisibility,
  updateStatus,
  visiblePaths,
}: TreeProps) {
  return hierarchy
    .treeRows(ancestorCode, codeToStatus, codeToTerm, visiblePaths)
    .map((row) => (
      <TreeRow
        key={row.path}
        code={row.code}
        hasDescendants={row.hasDescendants}
        isExpanded={row.isExpanded}
        path={row.path}
        pipes={row.pipes}
        showMoreInfoModal={showMoreInfoModal}
        status={row.status}
        term={row.term}
        toggleVisibility={toggleVisibility}
        updateStatus={updateStatus}
      />
    ));
}

export default Tree;
