import React from "react";
import Hierarchy from "../../_hierarchy";
import { PageData } from "../../types";
import Container from "../Codelist/Container";
import EmptySearch from "../Codelist/EmptySearch";

interface CodelistTabProps {
  allCodes: PageData["allCodes"];
  ancestorCodes?: string[];
  codeToStatus: PageData["codeToStatus"];
  codeToTerm: PageData["codeToTerm"];
  hierarchy: Hierarchy;
  isEditable: PageData["isEditable"];
  resultsHeading: PageData["resultsHeading"];
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
  treeTables,
  updateStatus,
  visiblePaths,
}: CodelistTabProps) {
  return (
    <>
      <h3 className="h4">{resultsHeading}</h3>
      <hr />
      {treeTables.length > 0 ? (
        <Container
          allCodes={allCodes}
          codeToStatus={codeToStatus}
          codeToTerm={codeToTerm}
          hierarchy={hierarchy}
          isEditable={isEditable}
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
