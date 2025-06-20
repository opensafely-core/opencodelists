import React from "react";
import { ListGroup, Badge as StatusBadge } from "react-bootstrap";
import { readValueFromPage } from "../../_utils";
import { PageData } from "../../types";
import ActionButtons from "../ActionButtons";
import { SummaryProps } from "../Cards/Summary";

export default function Header({
  counts,
  isEditable,
}: {
  counts: SummaryProps["counts"];
  isEditable: PageData["isEditable"];
}) {
  const codelistMetadata = readValueFromPage("metadata");

  return (
    <div className="border-bottom mb-3 pb-3">
      <div className="d-flex flex-row justify-content-between gap-2 mb-2">
        <h1 className="h3">
          {codelistMetadata.codelist_name}
          <StatusBadge className="align-text-bottom ml-1" variant="secondary">
            Draft
          </StatusBadge>
        </h1>

        {isEditable && <ActionButtons counts={counts} />}
      </div>

      {codelistMetadata && (
        <ListGroup horizontal className="small">
          <ListGroup.Item className="py-1 px-2">
            <dt>Coding system</dt>
            <dd className="mb-0">{codelistMetadata.coding_system_name}</dd>
          </ListGroup.Item>

          <ListGroup.Item className="py-1 px-2">
            <dt>Coding system release</dt>
            <dd className="mb-0">
              {codelistMetadata.coding_system_release.release_name}{" "}
              {codelistMetadata.coding_system_release.valid_from ? (
                <>({codelistMetadata.coding_system_release.valid_from})</>
              ) : null}
            </dd>
          </ListGroup.Item>

          {codelistMetadata.organisation_name ? (
            <ListGroup.Item className="py-1 px-2">
              <dt>Organisation</dt>
              <dd className="mb-0">{codelistMetadata.organisation_name}</dd>
            </ListGroup.Item>
          ) : null}

          <ListGroup.Item className="py-1 px-2">
            <dt>Codelist ID</dt>
            <dd className="mb-0">{codelistMetadata.codelist_full_slug}</dd>
          </ListGroup.Item>

          <ListGroup.Item className="py-1 px-2">
            <dt>Version ID</dt>
            <dd className="mb-0">{codelistMetadata.hash}</dd>
          </ListGroup.Item>
        </ListGroup>
      )}
    </div>
  );
}
