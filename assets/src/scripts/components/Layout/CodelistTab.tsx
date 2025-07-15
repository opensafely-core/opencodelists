import React from "react";
import Hierarchy from "../../_hierarchy";
import { PageData, ToggleVisibility } from "../../types";
import EmptySearch from "../EmptySearch";
import TreeTables from "../TreeTables";

interface CodelistTabProps {
  allCodes: PageData["allCodes"];
  ancestorCodes?: string[];
  codeToStatus: PageData["codeToStatus"];
  codeToTerm: PageData["codeToTerm"];
  hierarchy: Hierarchy;
  isEditable: PageData["isEditable"];
  resultsHeading: PageData["resultsHeading"];
  toggleVisibility: ToggleVisibility;
  treeTables: PageData["treeTables"];
  updateStatus: Function;
  visiblePaths: PageData["visiblePaths"];
}

export default function CodelistTab({
  allCodes,
  codeToStatus,
  codeToTerm,
  hierarchy,
  isEditable,
  resultsHeading,
  toggleVisibility,
  treeTables,
  updateStatus,
  visiblePaths,
}: CodelistTabProps) {
  return (
    <>
      <h3 className="h4">{resultsHeading}</h3>
      <hr />
      {treeTables.length > 0 ? (
        <TreeTables
          allCodes={allCodes}
          codeToStatus={codeToStatus}
          codeToTerm={codeToTerm}
          hierarchy={hierarchy}
          isEditable={isEditable}
          toggleVisibility={toggleVisibility}
          treeTables={treeTables}
          updateStatus={updateStatus}
          visiblePaths={visiblePaths}
        />
      ) : (
        <EmptySearch />
      )}
    </>
  );
}
