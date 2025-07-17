import React from "react";
import { SidebarContext, sidebarData } from "../../context/sidebar-context";
import SearchForm from "../Cards/SearchForm";
import Searches from "../Cards/Searches";
import Summary, { SummaryProps } from "../Cards/Summary";
import Tools from "../Cards/Tools";
import Versions from "../Cards/Versions";

export default function Sidebar({
  counts,
  isEmptyCodelist,
}: {
  counts: SummaryProps["counts"];
  isEmptyCodelist: boolean;
}) {
  return (
    <SidebarContext.Provider value={{ ...sidebarData }}>
      <div className="col-md-3 builder__sidebar">
        {isEmptyCodelist ? (
          <SearchForm />
        ) : (
          <>
            <Summary counts={counts} />
            <Searches />
            <SearchForm />
            <Versions />
          </>
        )}

        <Tools />
      </div>
    </SidebarContext.Provider>
  );
}
