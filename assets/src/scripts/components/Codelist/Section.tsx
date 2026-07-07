import React from "react";
import type Hierarchy from "../../_hierarchy";
import type { ICD10WarningIndicatorMap } from "../../icd10-warning-indicators";
import type {
  AncestorCodes,
  PageData,
  ToggleVisibility,
  UpdateStatus,
} from "../../types";
import Tree from "./Tree";

interface SectionProps {
  allCodes: PageData["allCodes"];
  ancestorCodes: AncestorCodes;
  codeToStatus: PageData["codeToStatus"];
  codeToTerm: PageData["codeToTerm"];
  heading: string;
  hierarchy: Hierarchy;
  icd10WarningIndicators: ICD10WarningIndicatorMap;
  isEditable: PageData["isEditable"];
  toggleVisibility: ToggleVisibility;
  updateStatus: UpdateStatus;
  visiblePaths: PageData["visiblePaths"];
}

export default function Section({
  allCodes,
  ancestorCodes,
  codeToStatus,
  codeToTerm,
  heading,
  hierarchy,
  icd10WarningIndicators,
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
            icd10WarningIndicators={icd10WarningIndicators}
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
