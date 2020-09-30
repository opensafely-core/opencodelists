"use strict";

import ReactDOM from "react-dom";
// Although React is not used in this module, if this line is removed, there is
// a runtime error in codelistbuilder.jsx.
import React from "react";

import CodelistBuilder from "./codelistbuilder";
import Hierarchy from "../hierarchy";
import { readValueFromPage } from "../utils";

const hierarchy = new Hierarchy(
  readValueFromPage("parent-map"),
  readValueFromPage("child-map")
);

ReactDOM.render(
  <CodelistBuilder
    searches={readValueFromPage("searches")}
    filter={readValueFromPage("filter")}
    tables={readValueFromPage("tables")}
    includedCodes={readValueFromPage("included-codes")}
    excludedCodes={readValueFromPage("excluded-codes")}
    displayedCodes={readValueFromPage("displayed-codes")}
    isEditable={readValueFromPage("is-editable")}
    updateURL={readValueFromPage("update-url")}
    searchURL={readValueFromPage("search-url")}
    hierarchy={hierarchy}
    downloadURL={readValueFromPage("download-url")}
  />,
  document.querySelector("#codelist-builder-container")
);
