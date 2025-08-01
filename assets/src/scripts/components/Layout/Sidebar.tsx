import React from "react";
import Searches from "../Cards/Searches";
import SearchForm from "../Cards/SearchForm";
import Summary, { type SummaryProps } from "../Cards/Summary";
import Tools from "../Cards/Tools";
import Versions from "../Cards/Versions";

export default function Sidebar({
  counts,
  isEditable,
  isEmptyCodelist,
}: {
  counts: SummaryProps["counts"];
  isEditable: boolean;
  isEmptyCodelist: boolean;
}) {
  return (
    <div className="col-md-3 builder__sidebar">
      {!isEmptyCodelist && <Summary counts={counts} />}
      <Searches />
      {isEditable && <SearchForm />}
      {!isEmptyCodelist && <Versions />}
      <Tools />
    </div>
  );
}
