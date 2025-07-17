import React from "react";
import { createContext } from "react";
import Hierarchy from "../../_hierarchy";
import { readValueFromPage } from "../../_utils";
import { PageData } from "../../types";
import Container from "../Codelist/Container";
import EmptySearch from "../Codelist/EmptySearch";

const pageData = {
  allCodes: readValueFromPage("all-codes"),
  codeToTerm: readValueFromPage("code-to-term"),
  isEditable: readValueFromPage("is-editable"),
};

// Define the context value type
interface CodelistContextType {
  allCodes: PageData["allCodes"];
  codeToTerm: PageData["codeToTerm"];
  isEditable: PageData["isEditable"];
  codeToStatus: PageData["codeToStatus"];
  hierarchy: Hierarchy;
  updateStatus: Function;
  visiblePaths: PageData["visiblePaths"];
}

export const CodelistContext = createContext<CodelistContextType>({
  ...pageData,
  codeToStatus: {},
  hierarchy: new Hierarchy([], new Set()),
  updateStatus: Function,
  visiblePaths: new Set<string>(),
});

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
