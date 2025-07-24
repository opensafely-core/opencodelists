import React from "react";
import { Form } from "react-bootstrap";
import type { PageData, Reference } from "../../types";
import type { MetadataFieldName } from "../CodelistBuilder";
import ReferenceList from "../Metadata/ReferenceList";

interface MetadataTabProps {
  handleSaveReferences: (references: Reference[]) => void;
  isEditable: PageData["isEditable"];
  references: Reference[];
  renderMetadataField: (field: MetadataFieldName) => React.ReactElement;
}

export default function MetadataTab({
  handleSaveReferences,
  isEditable,
  references,
  renderMetadataField,
}: MetadataTabProps) {
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
        <ReferenceList
          isEditable={isEditable}
          references={references}
          onSave={handleSaveReferences}
        />
      </Form>
    </>
  );
}
