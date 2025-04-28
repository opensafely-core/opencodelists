import React from "react";
import { ListGroup } from "react-bootstrap";
import { PageData } from "../types";

export default function Metadata({ data }: { data: PageData["metadata"] }) {
  return (
    <ListGroup horizontal className="small">
      <ListGroup.Item className="py-1 px-2">
        <dt>Coding system</dt>
        <dd className="mb-0">{data.coding_system_name}</dd>
      </ListGroup.Item>

      <ListGroup.Item className="py-1 px-2">
        <dt>Coding system release</dt>
        <dd className="mb-0">
          {data.coding_system_release.release_name}{" "}
          {data.coding_system_release.valid_from ? (
            <>({data.coding_system_release.valid_from})</>
          ) : null}
        </dd>
      </ListGroup.Item>

      {data.organisation_name ? (
        <ListGroup.Item className="py-1 px-2">
          <dt>Organisation</dt>
          <dd className="mb-0">{data.organisation_name}</dd>
        </ListGroup.Item>
      ) : null}

      <ListGroup.Item className="py-1 px-2">
        <dt>Codelist ID</dt>
        <dd className="mb-0">{data.codelist_full_slug}</dd>
      </ListGroup.Item>

      <ListGroup.Item className="py-1 px-2">
        <dt>Version ID</dt>
        <dd className="mb-0">{data.hash}</dd>
      </ListGroup.Item>
    </ListGroup>
  );
}
