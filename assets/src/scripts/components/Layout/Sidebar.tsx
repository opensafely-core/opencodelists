import React from "react";
import { readValueFromPage } from "../../_utils";
import { IS_EDITABLE, IS_EMPTY_CODELIST } from "../../types";
import SearchForm from "../Cards/SearchForm";
import Searches from "../Cards/Searches";
import Summary, { SummaryProps } from "../Cards/Summary";
import Tools from "../Cards/Tools";
import Versions from "../Cards/Versions";

export default function Sidebar({
  counts,
}: { counts: SummaryProps["counts"] }) {
  const isEditable: IS_EDITABLE = readValueFromPage("is-editable");
  const isEmptyCodelist: IS_EMPTY_CODELIST =
    readValueFromPage("is-empty-codelist");

  return (
    <>
      {!isEmptyCodelist && <Summary counts={counts} />}
      <Searches />
      {isEditable && <SearchForm />}
      {!isEmptyCodelist && <Versions />}
      <Tools />
    </>
  );
}
