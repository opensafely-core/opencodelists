/** biome-ignore-all lint/correctness/useUniqueElementIds: IDs required by elements */
import React from "react";
import MetadataForm from "../Metadata/MetadataForm";
import References from "../Metadata/References";

export default function MetadataTab() {
  return (
    <>
      <p className="font-italic">
        Users have found it helpful to record their decision strategy as they
        build their codelist. Text added here will be ready for you to edit
        before you publish the codelist.
      </p>
      <div className="builder__metadata-forms">
        <MetadataForm id="description" name="Description" rows={6} />
        <MetadataForm id="methodology" name="Methodology" rows={20} />
        <References />
      </div>
    </>
  );
}
