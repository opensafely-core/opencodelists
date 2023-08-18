"use strict";

import ReactDOM from "react-dom";
import React from "react";

import Hierarchy from "../hierarchy";
import TreeTables from "../common/tree-tables";
import { readValueFromPage } from "../utils";

const hierarchy = new Hierarchy(
  readValueFromPage("parent-map"),
  readValueFromPage("child-map"),
);

const treeTables = readValueFromPage("tree-tables");
const codeToStatus = readValueFromPage("code-to-status");
const codeToTerm = readValueFromPage("code-to-term");

const ancestorCodes = treeTables
  .map(([, ancestorCodes]) => ancestorCodes)
  .flat();
const visiblePaths = hierarchy.initiallyVisiblePaths(
  ancestorCodes,
  codeToStatus,
  0,
);

ReactDOM.render(
  <TreeTables
    hierarchy={hierarchy}
    treeTables={treeTables}
    codeToStatus={codeToStatus}
    codeToTerm={codeToTerm}
    visiblePaths={visiblePaths}
    updateStatus={null}
    showMoreInfoModal={null}
  />,
  document.querySelector("#codelist-tree"),
);
