import React, { StrictMode } from "react";
import { createRoot } from "react-dom/client";
import Hierarchy from "../_hierarchy";
import { readValueFromPage } from "../_utils";
import CodelistBuilder from "../components/CodelistBuilder";

const hierarchy = new Hierarchy(
  readValueFromPage("parent-map"),
  readValueFromPage("child-map"),
);

const treeTables = readValueFromPage("tree-tables");
const codeToStatus = readValueFromPage("code-to-status");
const codeToTerm = readValueFromPage("code-to-term");

const ancestorCodes = treeTables
  .map(([_, ancestorCodes]) => ancestorCodes)
  .flat();
const visiblePaths = hierarchy.initiallyVisiblePaths(
  ancestorCodes,
  codeToStatus,
  1,
);

const container = document.getElementById("codelist-builder-container");
if (container) {
  const root = createRoot(container);
  root.render(
    <StrictMode>
      <CodelistBuilder
        allCodes={readValueFromPage("all-codes")}
        codeToStatus={codeToStatus}
        codeToTerm={codeToTerm}
        draftURL={readValueFromPage("draft-url")}
        excludedCodes={readValueFromPage("excluded-codes")}
        filter={readValueFromPage("filter")}
        hierarchy={hierarchy}
        includedCodes={readValueFromPage("included-codes")}
        isEditable={readValueFromPage("is-editable")}
        metadata={readValueFromPage("metadata")}
        resultsHeading={readValueFromPage("results-heading")}
        searches={readValueFromPage("searches")}
        searchURL={readValueFromPage("search-url")}
        treeTables={treeTables}
        updateURL={readValueFromPage("update-url")}
        versions={readValueFromPage("versions")}
        visiblePaths={visiblePaths}
      />
    </StrictMode>,
  );
}
