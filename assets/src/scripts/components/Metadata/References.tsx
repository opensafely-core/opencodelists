import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import React, { useState } from "react";
import { postFetchWithOptions, readValueFromPage } from "../../_utils";
import type { IS_EDITABLE, METADATA } from "../../types";
import Reference from "./Reference";
import ReferenceForm from "./ReferenceForm";

export default function References() {
  const isEditable: IS_EDITABLE = readValueFromPage("is-editable");
  const apiURLs = readValueFromPage("api-urls");

  const [showAddReference, setShowAddReference] = useState(false);

  const queryClient = useQueryClient();
  const { data, isPending, isError } = useQuery({
    queryKey: ["references"],
    queryFn: async () => {
      const response = await fetch(
        apiURLs.references,
      );
      if (!response.ok) throw new Error("File list not found");
      return response.json();
    },
    select: (data: { references: METADATA["references"] }) => data.references,
  });

  const addReference = useMutation({
    mutationFn: async (updatedReferences: METADATA["references"]) => {
      return postFetchWithOptions({
        body: { references: updatedReferences },
        url: readValueFromPage("update-url"),
      });
    },
    onSuccess: (data) => {
      queryClient.setQueryData(["references"], data.metadata.references);
      setShowAddReference(false);
    },
  });

  if (isPending || isError) {
    return (
      <div className="card">
        <div className="card-header d-flex flex-row align-items-center">
          <h3 className="h5 mb-0 mr-auto">References</h3>
        </div>

        <div className="card-body">
          <p>
            Sometimes it's useful to provide links, for example links to
            algorithms, methodologies or papers that are relevant to this
            codelist.
          </p>
          {isPending && <p className="mb-0">Loading references&hellip;</p>}
          {isError && (
            <p className="mb-0 text-danger font-weight-bold">
              Unable to load references.
            </p>
          )}
        </div>
      </div>
    );
  }

  function handleSubmit(event: React.FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const currentReferences = queryClient.getQueryData([
      "references",
    ]) as METADATA["references"];
    const formData = new FormData(event.currentTarget);
    const formFieldData = Object.fromEntries(formData) as {
      text: string;
      url: string;
    };
    const updatedReferences = [...currentReferences, formFieldData];
    addReference.mutate(updatedReferences);
  }

  return (
    <div className="card">
      <div className="card-header d-flex flex-row align-items-center">
        <h3 className="h5 mb-0 mr-auto">References</h3>
        <button
          className="btn btn-primary btn-sm"
          onClick={() => setShowAddReference(true)}
          type="button"
        >
          Add {data.length ? "another" : "a"} reference
        </button>
      </div>

      <div className="card-body">
        <p className="mb-0">
          Sometimes it's useful to provide links, for example links to
          algorithms, methodologies or papers that are relevant to this
          codelist.
        </p>
      </div>

      {data.length || showAddReference ? (
        <ul className="list-group list-group-flush">
          {showAddReference && (
            <li className="list-group-item">
              <ReferenceForm
                onReset={() => setShowAddReference(false)}
                onSubmit={handleSubmit}
              />
            </li>
          )}

          {data.map((reference) => (
            <Reference
              isEditable={isEditable}
              key={reference.url}
              reference={reference}
            />
          ))}
        </ul>
      ) : null}
    </div>
  );
}
