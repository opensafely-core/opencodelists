import React from "react";
import { Col } from "react-bootstrap";
import Search from "../Search";
import SearchForm from "../SearchForm";
import Summary from "../Summary";
import Versions from "../Versions";

export default function Sidebar({
  counts,
  draftURL,
  isEditable,
  isEmptyCodelist,
  metadata,
  searches,
  searchURL,
  versions,
}: {
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
  metadata: {
    codelist_full_slug: string;
    codelist_name: string;
    coding_system_name: string;
    coding_system_release: {
      release_name: string;
      valid_from: string;
    };
    hash: string;
    organisation_name: string;
  };
  searches: {
    active: boolean;
    delete_url: string;
    term_or_code: string;
    url: string;
  }[];
  searchURL: string;
  versions: {
    created_at: string;
    current: boolean;
    status: string;
    tag_or_hash: string;
    url: string;
  }[];
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
        <SearchForm
          codingSystemName={metadata.coding_system_name}
          searchURL={searchURL}
        />
      )}

      <Versions versions={versions} />
    </Col>
  );
}
