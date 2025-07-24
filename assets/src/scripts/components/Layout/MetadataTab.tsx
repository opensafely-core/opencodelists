import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { ReactQueryDevtools } from "@tanstack/react-query-devtools";
import React from "react";
import { Form } from "react-bootstrap";
import type { PageData, Reference } from "../../types";
import type { MetadataFieldName } from "../CodelistBuilder";
import MetadataForm from "../Metadata/MetadataForm";
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
  const client = new QueryClient();

  return (
    <>
      <p className="font-italic">
        Users have found it helpful to record their decision strategy as they
        build their codelist. Text added here will be ready for you to edit
        before you publish the codelist.
      </p>

      <QueryClientProvider client={client}>
        <div className="builder__metadata-forms">
          <MetadataForm
            id="description"
            isEditable={isEditable}
            name="Description"
          />
          <MetadataForm
            id="methodology"
            isEditable={isEditable}
            name="Methodology"
          />
        </div>
        <ReactQueryDevtools />
      </QueryClientProvider>

      <Form noValidate>
        <ReferenceList
          isEditable={isEditable}
          references={references}
          onSave={handleSaveReferences}
        />
      </Form>
    </>
  );
}
