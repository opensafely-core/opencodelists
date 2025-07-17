import React, { StrictMode } from "react";
import { createRoot } from "react-dom/client";
import Hierarchy from "../_hierarchy";
import { readValueFromPage } from "../_utils";
import CodelistBuilder from "../components/CodelistBuilder";
import { CODE_TO_STATUS, CODE_TO_TERM, TREE_TABLES, VisiblePathsType } from "../types";

const hierarchy = new Hierarchy(
  readValueFromPage("parent-map"),
  readValueFromPage("child-map"),
);

const treeTables: TREE_TABLES = readValueFromPage("tree-tables");
const codeToStatus: CODE_TO_STATUS = readValueFromPage("code-to-status");
const codeToTerm: CODE_TO_TERM = readValueFromPage("code-to-term");

const ancestorCodes = treeTables
  .map(([_, ancestorCodes]) => ancestorCodes)
  .flat();

const visiblePaths: VisiblePathsType = hierarchy.initiallyVisiblePaths(
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
        hierarchy={hierarchy}
        isEditable={readValueFromPage("is-editable")}
        isEmptyCodelist={readValueFromPage("is-empty-codelist")}
        metadata={readValueFromPage("metadata")}
        resultsHeading={readValueFromPage("results-heading")}
        searches={readValueFromPage("searches")}
        searchURL={readValueFromPage("search-url")}
        sortByTerm={readValueFromPage("sortByTerm")}
        treeTables={treeTables}
        updateURL={readValueFromPage("update-url")}
        versions={readValueFromPage("versions")}
        visiblePaths={visiblePaths}
      />
    </StrictMode>,
  );
}
