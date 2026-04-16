import React, { useCallback, useState } from "react";
import type Hierarchy from "../../_hierarchy";
import type {
  CodeToUsage,
  PageData,
  Path,
  UpdateStatus,
  UsagePillDisplayOptions,
} from "../../types";
import Section from "./Section";

interface ContainerProps {
  allCodes: PageData["allCodes"];
  codeToStatus: PageData["codeToStatus"];
  codeToTerm: PageData["codeToTerm"];
  codeToUsage: CodeToUsage;
  hierarchy: Hierarchy;
  isEditable: PageData["isEditable"];
  treeTables: PageData["treeTables"];
  updateStatus: UpdateStatus;
  usagePillDisplayOptions: UsagePillDisplayOptions;
  visiblePaths: PageData["visiblePaths"];
}

export default function Container({
  allCodes,
  codeToStatus,
  codeToTerm,
  codeToUsage,
  hierarchy,
  isEditable,
  treeTables,
  updateStatus,
  usagePillDisplayOptions,
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
          codeToUsage={codeToUsage}
          heading={heading}
          hierarchy={hierarchy}
          isEditable={isEditable}
          toggleVisibility={handleToggleVisibility}
          updateStatus={updateStatus}
          usagePillDisplayOptions={usagePillDisplayOptions}
          visiblePaths={visiblePaths}
        />
      ))}
    </>
  );
}
