import React from "react";
import { Badge, ListGroup } from "react-bootstrap";
import { PageData } from "../../types";
import { SummaryProps } from "../Cards/Summary";
import ManagementForm from "../Header/ManagementForm";

export default function Header({
  counts,
  isEditable,
  metadata,
}: {
  counts: SummaryProps["counts"];
  isEditable: PageData["isEditable"];
  metadata: PageData["metadata"];
}) {
  return (
    <div className="border-bottom mb-3 pb-3">
      <div className="d-flex flex-row justify-content-between gap-2 mb-2">
        <h1 className="h3">
          {metadata.codelist_name}
          <Badge className="align-text-bottom ml-1" variant="secondary">
            Draft
          </Badge>
        </h1>
        {isEditable && <ManagementForm counts={counts} />}
      </div>

      <ListGroup horizontal className="small">
        <ListGroup.Item className="py-1 px-2">
          <dt>Coding system</dt>
          <dd className="mb-0">{metadata.coding_system_name}</dd>
        </ListGroup.Item>

        <ListGroup.Item className="py-1 px-2">
          <dt>Coding system release</dt>
          <dd className="mb-0">
            {metadata.coding_system_release.release_name}{" "}
            {metadata.coding_system_release.valid_from ? (
              <>({metadata.coding_system_release.valid_from})</>
            ) : null}
          </dd>
        </ListGroup.Item>

        {metadata.organisation_name ? (
          <ListGroup.Item className="py-1 px-2">
            <dt>Organisation</dt>
            <dd className="mb-0">{metadata.organisation_name}</dd>
          </ListGroup.Item>
        ) : null}

        <ListGroup.Item className="py-1 px-2">
          <dt>Codelist ID</dt>
          <dd className="mb-0">{metadata.codelist_full_slug}</dd>
        </ListGroup.Item>

        <ListGroup.Item className="py-1 px-2">
          <dt>Version ID</dt>
          <dd className="mb-0">{metadata.hash}</dd>
        </ListGroup.Item>
      </ListGroup>
    </div>
  );
}
