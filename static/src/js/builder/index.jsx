"use strict";

import ReactDOM from "react-dom";
import React from "react";

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

ReactDOM.render(
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
    updateURL={readValueFromPage("update-url")}
    searchURL={readValueFromPage("search-url")}
  />,
  document.querySelector("#codelist-builder-container")
);
