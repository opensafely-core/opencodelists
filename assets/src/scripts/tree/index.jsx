import React from "react";
import { createRoot } from "react-dom/client";
import Hierarchy from "../hierarchy";
import TreeTables from "../common/tree-tables";
import { readValueFromPage } from "../utils";

const hierarchy = new Hierarchy(
  readValueFromPage("parent-map"),
  readValueFromPage("child-map")
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
  0
);

const container = document.getElementById("codelist-tree");
const root = createRoot(container);
container
  ? root.render(
      <TreeTables
        hierarchy={hierarchy}
        treeTables={treeTables}
        codeToStatus={codeToStatus}
        codeToTerm={codeToTerm}
        visiblePaths={visiblePaths}
        updateStatus={null}
        showMoreInfoModal={null}
      />
    )
  : null;
