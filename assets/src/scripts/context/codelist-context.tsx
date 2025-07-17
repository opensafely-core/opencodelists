import { createContext, useContext } from "react";
import Hierarchy from "../_hierarchy";
import { readValueFromPage } from "../_utils";
import { PageData } from "../types";

interface CodelistContextType {
  allCodes: PageData["allCodes"];
  codeToTerm: PageData["codeToTerm"];
  isEditable: PageData["isEditable"];
  codeToStatus: PageData["codeToStatus"];
  hierarchy: Hierarchy;
  updateStatus: Function;
  visiblePaths: PageData["visiblePaths"];
}

export const pageData = {
  allCodes: readValueFromPage("all-codes"),
  codeToTerm: readValueFromPage("code-to-term"),
  isEditable: readValueFromPage("is-editable"),
};

export const CodelistContext = createContext<CodelistContextType>({
  ...pageData,
  codeToStatus: {},
  hierarchy: new Hierarchy([], new Set()),
  updateStatus: Function,
  visiblePaths: new Set<string>(),
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
