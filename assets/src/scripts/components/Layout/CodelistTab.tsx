import React from "react";
import { readValueFromPage } from "../../_utils";
import EmptySearch from "../EmptySearch";
import TreeTables from "../TreeTables";

export default function CodelistTab({
  allCodes,
  codeToStatus,
  hierarchy,
  isEditable,
  updateStatus,
  visiblePaths,
}) {
  const codeToTerm = readValueFromPage("code-to-term");
  const resultsHeading = readValueFromPage("results-heading");
  const treeTables = readValueFromPage("tree-tables");

  return (
    <>
      <h3 className="h4">{resultsHeading}</h3>
      <hr />
      {treeTables.length > 0 ? (
        <>
          <TreeTables
            allCodes={allCodes}
            codeToStatus={codeToStatus}
            codeToTerm={codeToTerm}
            hierarchy={hierarchy}
            isEditable={isEditable}
            treeTables={treeTables}
            updateStatus={updateStatus}
            visiblePaths={visiblePaths}
          />
        </>
      ) : (
        <EmptySearch />
      )}
    </>
  );
}
