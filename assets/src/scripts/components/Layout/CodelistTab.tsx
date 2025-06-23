import React, { useContext } from "react";
import { readValueFromPage } from "../../_utils";
import { BuilderContext } from "../../state/BuilderContext";
import { PageData } from "../../types";
import EmptySearch from "../Codelist/EmptySearch";
import TreeTables from "../Codelist/TreeTables";

export default function CodelistTab({
  codeToStatus,
  updateStatus,
  visiblePaths,
}: {
  codeToStatus: PageData["codeToStatus"];
  updateStatus: Function;
  visiblePaths: PageData["visiblePaths"];
}) {
  const resultsHeading = readValueFromPage("results-heading");
  const treeTables = readValueFromPage("tree-tables");
  const state = useContext(BuilderContext);

  return (
    <BuilderContext.Provider value={{ ...state, codeToStatus, visiblePaths }}>
      <h3 className="h4">{resultsHeading}</h3>
      <hr />
      {treeTables.length > 0 ? (
        <TreeTables treeTables={treeTables} updateStatus={updateStatus} />
      ) : (
        <EmptySearch />
      )}
    </BuilderContext.Provider>
  );
}
