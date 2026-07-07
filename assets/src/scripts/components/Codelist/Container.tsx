import React, { useCallback, useState } from "react";
import type Hierarchy from "../../_hierarchy";
import type { ICD10WarningIndicatorMap } from "../../icd10-warning-indicators";
import type { PageData, Path, UpdateStatus } from "../../types";
import Section from "./Section";

interface ContainerProps {
  allCodes: PageData["allCodes"];
  codeToStatus: PageData["codeToStatus"];
  codeToTerm: PageData["codeToTerm"];
  hierarchy: Hierarchy;
  icd10WarningIndicators: ICD10WarningIndicatorMap;
  isEditable: PageData["isEditable"];
  treeTables: PageData["treeTables"];
  updateStatus: UpdateStatus;
  visiblePaths: PageData["visiblePaths"];
}

export default function Container({
  allCodes,
  codeToStatus,
  codeToTerm,
  hierarchy,
  icd10WarningIndicators,
  isEditable,
  treeTables,
  updateStatus,
  visiblePaths: initialVisiblePaths,
}: ContainerProps) {
  const [visiblePaths, setVisiblePaths] = useState(initialVisiblePaths);

  const handleToggleVisibility = useCallback(
    (path: Path) => {
      setVisiblePaths((prevVisiblePaths) => {
        const newVisiblePaths = new Set(prevVisiblePaths);
        hierarchy.toggleVisibility(newVisiblePaths, path);
        return newVisiblePaths;
      });
    },
    [hierarchy],
  );

  return (
    <>
      {treeTables.map(([heading, ancestorCodes]) => (
        <Section
          key={heading}
          allCodes={allCodes}
          ancestorCodes={ancestorCodes}
          codeToStatus={codeToStatus}
          codeToTerm={codeToTerm}
          heading={heading}
          hierarchy={hierarchy}
          icd10WarningIndicators={icd10WarningIndicators}
          isEditable={isEditable}
          toggleVisibility={handleToggleVisibility}
          updateStatus={updateStatus}
          visiblePaths={visiblePaths}
        />
      ))}
    </>
  );
}
