import React from "react";
import type Hierarchy from "../../_hierarchy";
import { readValueFromPage } from "../../_utils";
import type {
  AncestorCode,
  CodeToUsage,
  PageData,
  ToggleVisibility,
  UpdateStatus,
  UsagePillDisplayOptions,
} from "../../types";
import Row from "./Row";

interface TreeProps {
  allCodes: PageData["allCodes"];
  ancestorCode: AncestorCode;
  codeToStatus: PageData["codeToStatus"];
  codeToTerm: PageData["codeToTerm"];
  codeToUsage: CodeToUsage;
  hierarchy: Hierarchy;
  isEditable: PageData["isEditable"];
  toggleVisibility: ToggleVisibility;
  updateStatus: UpdateStatus;
  usagePillDisplayOptions: UsagePillDisplayOptions;
  visiblePaths: PageData["visiblePaths"];
}

export default function Tree({
  allCodes,
  ancestorCode,
  codeToStatus,
  codeToTerm,
  codeToUsage,
  hierarchy,
  isEditable,
  toggleVisibility,
  updateStatus,
  usagePillDisplayOptions,
  visiblePaths,
}: TreeProps) {
  const sortByTerm: PageData["sortByTerm"] = readValueFromPage("sort-by-term");
  return hierarchy
    .treeRows(ancestorCode, codeToStatus, codeToTerm, visiblePaths, sortByTerm)
    .map((row) => (
      <Row
        allCodes={allCodes}
        code={row.code}
        codeToStatus={codeToStatus}
        codeToTerm={codeToTerm}
        codeToUsage={codeToUsage}
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
        usagePillDisplayOptions={usagePillDisplayOptions}
      />
    ));
}
