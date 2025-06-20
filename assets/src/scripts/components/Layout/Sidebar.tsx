import React from "react";
import { Col } from "react-bootstrap";
import Search, { SearchProps } from "../Search";
import SearchForm from "../SearchForm";
import Summary, { SummaryProps } from "../Summary";
import Versions from "../Versions";

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
  searches: SearchProps["searches"];
}) {
  return (
    <Col className="builder__sidebar" md="3">
      {!isEmptyCodelist && <Summary counts={counts} draftURL={draftURL} />}

      {searches.length > 0 && (
        <Search
          draftURL={draftURL}
          isEditable={isEditable}
          searches={searches}
        />
      )}

      {isEditable && <SearchForm />}

      <Versions />
    </Col>
  );
}
