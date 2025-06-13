import React from "react";
import { Form } from "react-bootstrap";
import ReferenceList from "./ReferenceList";
import MetadataField from "./MetadataField";
import { getFetchOptions } from "../../_utils";

export default function MetadataTab({
  metadata,
  references,
  setState,
  updateURL,
}) {
  const handleSaveReferences = async (
    newReferences: Array<{ text: string; url: string }>,
  ) => {
    const fetchOptions = getFetchOptions({ references: newReferences });
    try {
      await fetch(updateURL, fetchOptions);
      setState({
        metadata: { ...metadata, references: newReferences },
      });
    } catch (error) {
      console.error("Failed to save references:", error);
    }
  };

  return (
    <div style={{ maxWidth: "80ch" }}>
      <p style={{ fontStyle: "italic" }}>
        Users have found it helpful to record their decision strategy as they
        build their codelist. Text added here will be ready for you to edit
        before you publish the codelist.
      </p>
      <Form noValidate>
        <MetadataField field="description" metadata={metadata} updateURL={updateURL} />
        <MetadataField field="methodology" metadata={metadata} updateURL={updateURL} />
        <ReferenceList references={references} onSave={handleSaveReferences} />
      </Form>
    </div>
  );
}
