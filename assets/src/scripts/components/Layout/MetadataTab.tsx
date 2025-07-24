import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { ReactQueryDevtools } from "@tanstack/react-query-devtools";
import React from "react";
import MetadataForm from "../Metadata/MetadataForm";
import References from "../Metadata/References";

export default function MetadataTab() {
  const client = new QueryClient();

  return (
    <QueryClientProvider client={client}>
      <p className="font-italic">
        Users have found it helpful to record their decision strategy as they
        build their codelist. Text added here will be ready for you to edit
        before you publish the codelist.
      </p>
      <div className="builder__metadata-forms">
        <MetadataForm id="description" name="Description" />
        <MetadataForm id="methodology" name="Methodology" />
        <References />
      </div>
      <ReactQueryDevtools />
    </QueryClientProvider>
  );
}
