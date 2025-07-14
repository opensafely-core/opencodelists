import React from "react";
import { Form } from "react-bootstrap";
import ReferenceList from "../ReferenceList";

export default function MetadataTab({
  handleSaveReferences,
  renderMetadataField,
  references,
}) {
  return (
    <>
      <p className="font-italic">
        Users have found it helpful to record their decision strategy as they
        build their codelist. Text added here will be ready for you to edit
        before you publish the codelist.
      </p>
      <Form noValidate>
        {renderMetadataField("description")}
        {renderMetadataField("methodology")}
        <ReferenceList references={references} onSave={handleSaveReferences} />
      </Form>
    </>
  );
}
