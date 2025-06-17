import React from "react";
import { PageData } from "../../types";
import MetadataField from "./MetadataField";
import References from "./References";

export default function MetadataTab({
  metadata,
  updateURL,
}: {
  metadata: {
    description: {
      text: string;
      html: string;
      isEditing: boolean;
    };
    methodology: {
      text: string;
      html: string;
      isEditing: boolean;
    };
    references: {
      text: string;
      url: string;
    }[];
  };
  updateURL: PageData["updateURL"];
}) {
  return (
    <div style={{ maxWidth: "80ch" }}>
      <p>
        Record your decision strategy as you build your codelist. You can edit
        text added here again before you publish the codelist.
      </p>
      <MetadataField
        field="description"
        label="Description"
        metadata={metadata}
        updateURL={updateURL}
      />
      <MetadataField
        field="methodology"
        label="Methodology"
        metadata={metadata}
        updateURL={updateURL}
      />
      <References references={metadata.references} />
    </div>
  );
}
