import React from "react";
import { CodelistContext, codelistData } from "../../context/codelist-context";
import {
  CODE_TO_STATUS,
  RESULTS_HEADING,
  TREE_TABLES,
  UpdateStatusType,
  VisiblePathsType,
} from "../../types";
import Container from "../Codelist/Container";
import EmptySearch from "../Codelist/EmptySearch";

export default function CodelistTab({
  codeToStatus,
  resultsHeading,
  treeTables,
  updateStatus,
  visiblePaths,
}: {
  codeToStatus: CODE_TO_STATUS;
  resultsHeading: RESULTS_HEADING;
  treeTables: TREE_TABLES;
  updateStatus: UpdateStatusType;
  visiblePaths: VisiblePathsType;
}) {
  return (
    <CodelistContext.Provider
      value={{
        ...codelistData,
        codeToStatus,
        treeTables,
        updateStatus,
        visiblePaths,
      }}
    >
      <h3 className="h4">{resultsHeading}</h3>
      <hr />
      {treeTables.length > 0 ? (
        <Container updateStatus={updateStatus} />
      ) : (
        <EmptySearch />
      )}
    </CodelistContext.Provider>
  );
}
