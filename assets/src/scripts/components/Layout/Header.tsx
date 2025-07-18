import React from "react";
import { readValueFromPage } from "../../_utils";
import { IS_EDITABLE, METADATA, } from "../../types";
import { SummaryProps } from "../Cards/Summary";
import ManagementForm from "../Header/ManagementForm";

export default function Header({ counts }: { counts: SummaryProps["counts"] }) {
  const isEditable: IS_EDITABLE = readValueFromPage("is-editable");
  const metadata: METADATA = readValueFromPage("metadata");
  const data = {
    codelistName: metadata?.codelist_name || "Could not load codelist name",
    codingSystemName: metadata?.coding_system_name,
    releaseName: metadata?.coding_system_release?.release_name,
    releaseValidFrom: metadata?.coding_system_release?.valid_from,
    orgName: metadata?.organisation_name,
    codelistID: metadata?.codelist_full_slug,
    versionID: metadata?.hash,
  };

  return (
    <div className="border-bottom mb-3 pb-3">
      <div className="d-flex flex-row justify-content-between gap-2 mb-2">
        <h1 className="h3">
          {data.codelistName}
          <span className="align-text-bottom ml-1 badge badge-secondary">
            Draft
          </span>
        </h1>
        {isEditable && <ManagementForm counts={counts} />}
      </div>

      {metadata && (
        <dl className="small list-group list-group-horizontal">
          {data.codingSystemName && (
            <div className="py-1 px-2 list-group-item">
              <dt>Coding system</dt>
              <dd className="mb-0">{data.codingSystemName}</dd>
            </div>
          )}

          {data.releaseName && (
            <div className="py-1 px-2 list-group-item">
              <dt>Coding system release</dt>
              <dd className="mb-0">
                {data.releaseName} {data.releaseValidFrom && <>({data.releaseValidFrom})</>}
              </dd>
            </div>
          )}

          {data.orgName && (
            <div className="py-1 px-2 list-group-item">
              <dt>Organisation</dt>
              <dd className="mb-0">{data.orgName}</dd>
            </div>
          )}

          {data.codelistID && (
            <div className="py-1 px-2 list-group-item">
              <dt>Codelist ID</dt>
              <dd className="mb-0">{data.codelistID}</dd>
            </div>
          )}

            {data.versionID && (
            <div className="py-1 px-2 list-group-item">
              <dt>Version ID</dt>
              <dd className="mb-0">{data.versionID}</dd>
            </div>
          )}
        </dl>
      )}
    </div>
  );
}
