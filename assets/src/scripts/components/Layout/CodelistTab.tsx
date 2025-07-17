import React from "react";
import Hierarchy from "../../_hierarchy";
import { CodelistContext, pageData } from "../../context/codelist-context";
import { PageData } from "../../types";
import Container from "../Codelist/Container";
import EmptySearch from "../Codelist/EmptySearch";

export default function CodelistTab({
  codeToStatus,
  hierarchy,
  resultsHeading,
  treeTables,
  updateStatus,
  visiblePaths,
}: {
  codeToStatus: PageData["codeToStatus"];
  hierarchy: Hierarchy;
  resultsHeading: PageData["resultsHeading"];
  treeTables: PageData["treeTables"];
  updateStatus: Function;
  visiblePaths: PageData["visiblePaths"];
}) {
  return (
    <CodelistContext.Provider
      value={{
        ...pageData,
        codeToStatus,
        hierarchy,
        updateStatus,
        visiblePaths,
      }}
    >
      <h3 className="h4">{resultsHeading}</h3>
      <hr />
      {treeTables.length > 0 ? (
        <Container
          hierarchy={hierarchy}
          treeTables={treeTables}
          updateStatus={updateStatus}
        />
      ) : (
        <EmptySearch />
      )}
    </CodelistContext.Provider>
  );
}
