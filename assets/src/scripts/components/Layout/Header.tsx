import React from "react";
import type { PageData } from "../../types";
import type { SummaryProps } from "../Cards/Summary";
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
          <span className="badge badge-secondary align-text-bottom ml-1">
            Draft
          </span>
        </h1>
        {isEditable && <ManagementForm counts={counts} />}
      </div>

      <dl className="list-group list-group-horizontal small">
        <div className="list-group-item py-1 px-2">
          <dt>Coding system</dt>
          <dd className="mb-0">{metadata.coding_system_name}</dd>
        </div>

        <div className="list-group-item py-1 px-2">
          <dt>Coding system release</dt>
          <dd className="mb-0">
            {metadata.coding_system_release.release_name}{" "}
            {metadata.coding_system_release.valid_from ? (
              <>({metadata.coding_system_release.valid_from})</>
            ) : null}
          </dd>
        </div>

        {metadata.organisation_name ? (
          <div className="list-group-item py-1 px-2">
            <dt>Organisation</dt>
            <dd className="mb-0">{metadata.organisation_name}</dd>
          </div>
        ) : null}

        <div className="list-group-item py-1 px-2">
          <dt>Codelist ID</dt>
          <dd className="mb-0">{metadata.codelist_full_slug}</dd>
        </div>

        <div className="list-group-item py-1 px-2">
          <dt>Version ID</dt>
          <dd className="mb-0">{metadata.hash}</dd>
        </div>
      </dl>
    </div>
  );
}
