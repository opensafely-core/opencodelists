import React from "react";
import type Hierarchy from "../../_hierarchy";
import type { ICD10WarningIndicatorMap } from "../../icd10-warning-indicators";
import type { PageData, UpdateStatus } from "../../types";
import Container from "../Codelist/Container";
import EmptySearch from "../Codelist/EmptySearch";

interface CodelistTabProps {
  allCodes: PageData["allCodes"];
  ancestorCodes?: string[];
  codeToStatus: PageData["codeToStatus"];
  codeToTerm: PageData["codeToTerm"];
  hierarchy: Hierarchy;
  icd10WarningIndicators: ICD10WarningIndicatorMap;
  isEditable: PageData["isEditable"];
  resultsHeading: PageData["resultsHeading"];
  treeTables: PageData["treeTables"];
  updateStatus: UpdateStatus;
  visiblePaths: PageData["visiblePaths"];
}

export default function CodelistTab({
  allCodes,
  codeToStatus,
  codeToTerm,
  hierarchy,
  icd10WarningIndicators,
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
          icd10WarningIndicators={icd10WarningIndicators}
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
