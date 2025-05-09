import React, { StrictMode } from "react";
import { createRoot } from "react-dom/client";
import Hierarchy from "../_hierarchy";
import { readValueFromPage } from "../_utils";
import TreeTables from "../components/TreeTables";
import { PageData } from "../types";

const hierarchy = new Hierarchy(
  readValueFromPage("parent-map"),
  readValueFromPage("child-map"),
);

const treeTables: PageData["treeTables"] = readValueFromPage("tree-tables");
const codeToStatus: PageData["codeToStatus"] =
  readValueFromPage("code-to-status");
const codeToTerm: PageData["codeToTerm"] = readValueFromPage("code-to-term");

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
        allCodes={readValueFromPage("all-codes")}
        codeToStatus={codeToStatus}
        codeToTerm={codeToTerm}
        hierarchy={hierarchy}
        isEditable={false}
        treeTables={treeTables}
        toggleVisibility={() => null}
        updateStatus={() => null}
        visiblePaths={visiblePaths}
      />
    </StrictMode>,
  );
}
