import React from "react";
import type Hierarchy from "../../_hierarchy";
import { readValueFromPage } from "../../_utils";
import type { ICD10WarningIndicatorMap } from "../../icd10-warning-indicators";
import type {
  AncestorCode,
  PageData,
  ToggleVisibility,
  UpdateStatus,
} from "../../types";
import Row from "./Row";

interface TreeProps {
  allCodes: PageData["allCodes"];
  ancestorCode: AncestorCode;
  codeToStatus: PageData["codeToStatus"];
  codeToTerm: PageData["codeToTerm"];
  hierarchy: Hierarchy;
  icd10WarningIndicators: ICD10WarningIndicatorMap;
  isEditable: PageData["isEditable"];
  toggleVisibility: ToggleVisibility;
  updateStatus: UpdateStatus;
  visiblePaths: PageData["visiblePaths"];
}

export default function Tree({
  allCodes,
  ancestorCode,
  codeToStatus,
  codeToTerm,
  hierarchy,
  icd10WarningIndicators,
  isEditable,
  toggleVisibility,
  updateStatus,
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
        hasDescendants={row.hasDescendants}
        hierarchy={hierarchy}
        icd10WarningIndicator={icd10WarningIndicators[row.code.toUpperCase()]}
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
