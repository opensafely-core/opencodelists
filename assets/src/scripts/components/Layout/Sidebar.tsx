import React from "react";
import { Col } from "react-bootstrap";
import SearchForm from "../Cards/SearchForm";
import Searches, { SearchesProps } from "../Cards/Searches";
import Summary, { SummaryProps } from "../Cards/Summary";
import Tools from "../Cards/Tools";
import Versions from "../Cards/Versions";

export default function Sidebar({
  counts,
  draftURL,
  isEditable,
  isEmptyCodelist,
  searches,
}: {
  counts: SummaryProps["counts"];
  draftURL: string;
  isEditable: boolean;
  isEmptyCodelist: boolean;
  searches: SearchesProps["searches"];
}) {
  return (
    <Col className="builder__sidebar" md="3">
      {!isEmptyCodelist && <Summary counts={counts} draftURL={draftURL} />}
      {searches.length > 0 && (
        <Searches
          draftURL={draftURL}
          isEditable={isEditable}
          searches={searches}
        />
      )}
      {isEditable && <SearchForm />}
      {!isEmptyCodelist && <Versions />}
      <Tools />
    </Col>
  );
}
