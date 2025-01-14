import React, { StrictMode } from "react";
import { createRoot } from "react-dom/client";
import Hierarchy from "../_hierarchy";
import { readValueFromPage } from "../_utils";
import TreeTables from "../components/TreeTables";

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

const container = document.getElementById("codelist-tree");
if (container) {
  const root = createRoot(container);
  root.render(
    <StrictMode>
      <TreeTables
        codeToStatus={codeToStatus}
        codeToTerm={codeToTerm}
        hierarchy={hierarchy}
        showMoreInfoModal={null}
        treeTables={treeTables}
        updateStatus={null}
        visiblePaths={visiblePaths}
      />
    </StrictMode>,
  );
}
