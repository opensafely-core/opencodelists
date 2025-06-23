import React from "react";
import { Form } from "react-bootstrap";
import { Reference } from "../../types";
import ReferenceList from "../Metadata/ReferenceList";

export default function MetadataTab({
  handleSaveReferences,
  references,
  renderMetadataField,
}: {
  handleSaveReferences: (references: Reference[]) => void;
  references: Reference[];
  renderMetadataField: Function;
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
