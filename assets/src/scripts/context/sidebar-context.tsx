import { createContext, useContext } from "react";
import { readValueFromPage } from "../_utils";
import { PageData } from "../types";

interface SidebarContextType {
  draftURL: PageData["draftURL"];
  isEditable: PageData["isEditable"];
  metadata: PageData["metadata"];
  searches: PageData["searches"];
  searchURL: PageData["searchURL"];
  versions: PageData["versions"];
}

export const sidebarData = {
  draftURL: readValueFromPage("draft-url"),
  isEditable: readValueFromPage("is-editable"),
  metadata: readValueFromPage("metadata"),
  searches: readValueFromPage("searches"),
  searchURL: readValueFromPage("search-url"),
  versions: readValueFromPage("versions"),
};

export const SidebarContext = createContext<SidebarContextType>({
  ...sidebarData,
});

export const useSidebarContext = () => {
  const sidebarContext = useContext(SidebarContext);

  if (!sidebarContext) {
    throw new Error(
      "useSidebarContext has to be used within <SidebarContext.Provider>",
    );
  }

  return sidebarContext;
};
