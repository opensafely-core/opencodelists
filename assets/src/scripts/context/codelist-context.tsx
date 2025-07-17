import { createContext, useContext } from "react";
import Hierarchy from "../_hierarchy";
import { readValueFromPage } from "../_utils";
import {
  ALL_CODES,
  CODE_TO_STATUS,
  CODE_TO_TERM,
  Code,
  IS_EDITABLE,
  METADATA,
  SORT_BY_TERM,
  TREE_TABLES,
  UpdateStatusType,
  VisiblePathsType,
} from "../types";

interface CodelistContextType {
  allCodes: ALL_CODES;
  codeToTerm: CODE_TO_TERM;
  isEditable: IS_EDITABLE;
  codeToStatus: CODE_TO_STATUS;
  hierarchy: Hierarchy;
  metadata: METADATA;
  sortByTerm: SORT_BY_TERM;
  treeTables: TREE_TABLES;
  updateStatus: UpdateStatusType;
  visiblePaths: VisiblePathsType;
}

export const codelistData = {
  allCodes: readValueFromPage("all-codes"),
  codeToTerm: readValueFromPage("code-to-term"),
  hierarchy: new Hierarchy(
    readValueFromPage("parent-map"),
    readValueFromPage("child-map"),
  ),
  isEditable: readValueFromPage("is-editable"),
  metadata: readValueFromPage("metadata"),
  sortByTerm: readValueFromPage("sort-by-term"),
};

export const CodelistContext = createContext<CodelistContextType>({
  ...codelistData,
  codeToStatus: {},
  treeTables: [],
  updateStatus: Function,
  visiblePaths: new Set<Code>(),
});

export const useCodelistContext = () => {
  const codelistContext = useContext(CodelistContext);

  if (!codelistContext) {
    throw new Error(
      "useCodelistContext has to be used within <CodelistContext.Provider>",
    );
  }

  return codelistContext;
};
