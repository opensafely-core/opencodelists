import React, { useState, useCallback } from "react";
import Hierarchy from "../../_hierarchy";
import { PageData, Path } from "../../types";
import TreeTable from "../TreeTable";

interface ContainerProps {
  allCodes: PageData["allCodes"];
  codeToStatus: PageData["codeToStatus"];
  codeToTerm: PageData["codeToTerm"];
  hierarchy: Hierarchy;
  isEditable: PageData["isEditable"];
  treeTables: PageData["treeTables"];
  updateStatus: Function;
  visiblePaths: PageData["visiblePaths"];
}

export default function Container({
  allCodes,
  codeToStatus,
  codeToTerm,
  hierarchy,
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
        <TreeTable
          key={heading}
          allCodes={allCodes}
          ancestorCodes={ancestorCodes}
          codeToStatus={codeToStatus}
          codeToTerm={codeToTerm}
          heading={heading}
          hierarchy={hierarchy}
          isEditable={isEditable}
          toggleVisibility={handleToggleVisibility}
          updateStatus={updateStatus}
          visiblePaths={visiblePaths}
        />
      ))}
    </>
  );
}
