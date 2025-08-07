import React from "react";
import { readValueFromPage } from "../../_utils";
import type { BUILDER_CONFIG } from "../../types";
import type { SummaryProps } from "../Cards/Summary";
import ManagementForm from "../Header/ManagementForm";

export default function Header({ counts }: { counts: SummaryProps["counts"] }) {
  const { codelist, coding_system }: BUILDER_CONFIG =
    readValueFromPage("builder-config");

  return (
    <div className="border-bottom mb-3 pb-3">
      <div className="d-flex flex-row justify-content-between gap-2 mb-2">
        <h1 className="h3">
          {codelist.name}
          <span className="badge badge-secondary align-text-bottom ml-1">
            Draft
          </span>
        </h1>
        {codelist.is_editable && <ManagementForm counts={counts} />}
      </div>

      <dl className="list-group list-group-horizontal small">
        <div className="list-group-item py-1 px-2">
          <dt>Coding system</dt>
          <dd className="mb-0">{coding_system.name}</dd>
        </div>

        <div className="list-group-item py-1 px-2">
          <dt>Coding system release</dt>
          <dd className="mb-0">
            {coding_system.release.name}{" "}
            {coding_system.release.valid_from_date ? (
              <>({coding_system.release.valid_from_date})</>
            ) : null}
          </dd>
        </div>

        {codelist.organisation ? (
          <div className="list-group-item py-1 px-2">
            <dt>Organisation</dt>
            <dd className="mb-0">{codelist.organisation}</dd>
          </div>
        ) : null}

        <div className="list-group-item py-1 px-2">
          <dt>Codelist ID</dt>
          <dd className="mb-0">{codelist.full_slug}</dd>
        </div>

        <div className="list-group-item py-1 px-2">
          <dt>Version ID</dt>
          <dd className="mb-0">{codelist.hash}</dd>
        </div>
      </dl>
    </div>
  );
}
