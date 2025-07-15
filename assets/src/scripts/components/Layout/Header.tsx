import React from "react";
import { PageData } from "../../types";
import { SummaryProps } from "../Cards/Summary";
import ManagementForm from "../ManagementForm";
import Metadata from "../Metadata";
import Title from "../Title";

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
        <Title name={metadata.codelist_name} />
        {isEditable && <ManagementForm counts={counts} />}
      </div>
      <Metadata data={metadata} />
    </div>
  );
}
