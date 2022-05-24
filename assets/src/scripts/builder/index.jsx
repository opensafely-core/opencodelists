import React from "react";
import { createRoot } from "react-dom/client";
import CodelistBuilder from "./codelistbuilder";
import Hierarchy from "../hierarchy";
import { readValueFromPage } from "../utils";

const hierarchy = new Hierarchy(
  readValueFromPage("parent-map"),
  readValueFromPage("child-map")
);

const treeTables = readValueFromPage("tree-tables");
const codeToStatus = readValueFromPage("code-to-status");
const codeToTerm = readValueFromPage("code-to-term");

const ancestorCodes = treeTables
  .map(([_, ancestorCodes]) => ancestorCodes) // eslint-disable-line no-unused-vars
  .flat();
const visiblePaths = hierarchy.initiallyVisiblePaths(
  ancestorCodes,
  codeToStatus,
  1
);

const container = document.getElementById("#codelist-builder-container");
const root = createRoot(container);

root.render(
  <CodelistBuilder
    resultsHeading={readValueFromPage("results-heading")}
    searches={readValueFromPage("searches")}
    filter={readValueFromPage("filter")}
    hierarchy={hierarchy}
    treeTables={treeTables}
    codeToStatus={codeToStatus}
    codeToTerm={codeToTerm}
    visiblePaths={visiblePaths}
    allCodes={readValueFromPage("all-codes")}
    includedCodes={readValueFromPage("included-codes")}
    excludedCodes={readValueFromPage("excluded-codes")}
    isEditable={readValueFromPage("is-editable")}
    draftURL={readValueFromPage("draft-url")}
    updateURL={readValueFromPage("update-url")}
    searchURL={readValueFromPage("search-url")}
    versions={readValueFromPage("versions")}
    metadata={readValueFromPage("metadata")}
  />
);
