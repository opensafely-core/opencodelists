import { createContext } from "react";
import Hierarchy from "../_hierarchy";
import { readValueFromPage } from "../_utils";
import { PageData } from "../types";

export const BuilderContext = createContext({
  codeToStatus: {} as PageData["codeToStatus"],
  codeToTerm: readValueFromPage("code-to-term") as PageData["codeToTerm"],
  hierarchy: new Hierarchy(
    readValueFromPage("parent-map"),
    readValueFromPage("child-map"),
  ),
  isEditable: readValueFromPage("is-editable") as PageData["isEditable"],
  visiblePaths: new Set() as PageData["visiblePaths"],
});
