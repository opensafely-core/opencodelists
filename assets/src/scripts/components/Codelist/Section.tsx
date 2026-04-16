import React from "react";
import type Hierarchy from "../../_hierarchy";
import type {
  AncestorCodes,
  CodeToUsage,
  PageData,
  ToggleVisibility,
  UpdateStatus,
  UsagePillDisplayOptions,
} from "../../types";
import Tree from "./Tree";

interface SectionProps {
  allCodes: PageData["allCodes"];
  ancestorCodes: AncestorCodes;
  codeToStatus: PageData["codeToStatus"];
  codeToTerm: PageData["codeToTerm"];
  codeToUsage: CodeToUsage;
  heading: string;
  hierarchy: Hierarchy;
  isEditable: PageData["isEditable"];
  toggleVisibility: ToggleVisibility;
  updateStatus: UpdateStatus;
  usagePillDisplayOptions: UsagePillDisplayOptions;
  visiblePaths: PageData["visiblePaths"];
}

export default function Section({
  allCodes,
  ancestorCodes,
  codeToStatus,
  codeToTerm,
  codeToUsage,
  heading,
  hierarchy,
  isEditable,
  toggleVisibility,
  updateStatus,
  usagePillDisplayOptions,
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
            codeToUsage={codeToUsage}
            hierarchy={hierarchy}
            isEditable={isEditable}
            key={ancestorCode}
            toggleVisibility={toggleVisibility}
            updateStatus={updateStatus}
            usagePillDisplayOptions={usagePillDisplayOptions}
            visiblePaths={visiblePaths}
          />
        ))}
      </div>
    </div>
  );
}
