import React from "react";
import { Col } from "react-bootstrap";
import Search from "../Search";
import SearchForm from "../SearchForm";
import Summary from "../Summary";
import Versions from "../Versions";

export default function Sidebar({
  codingSystemName,
  counts,
  draftURL,
  isEditable,
  isEmptyCodelist,
  searches,
  searchURL,
}: {
  codingSystemName: string;
  counts: {
    "!": number;
    "(+)": number;
    "(-)": number;
    "+": number;
    "-": number;
    "?": number;
    total: number;
  };
  draftURL: string;
  isEditable: boolean;
  isEmptyCodelist: boolean;
  searches: {
    active: boolean;
    delete_url: string;
    term_or_code: string;
    url: string;
  }[];
  searchURL: string;
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

      {isEditable && (
        <SearchForm codingSystemName={codingSystemName} searchURL={searchURL} />
      )}

      <Versions />
    </Col>
  );
}
