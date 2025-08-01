import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import React, { useState } from "react";
import { postFetchWithOptions, readValueFromPage } from "../../_utils";
import type { IS_EDITABLE, METADATA } from "../../types";
import Reference from "./Reference";
import ReferenceForm from "./ReferenceForm";

export default function References() {
  const isEditable: IS_EDITABLE = readValueFromPage("is-editable");
  const references: METADATA["references"] =
    readValueFromPage("metadata")?.references;

  const [showAddReference, setShowAddReference] = useState(false);

  const queryClient = useQueryClient();
  const { data } = useQuery({
    queryKey: ["references"],
    initialData: references,
    queryFn: () => references,
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

  if (!Array.isArray(references) || !data) return null;

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
        {isEditable ? (
          <button
            className="btn btn-primary btn-sm"
            onClick={() => setShowAddReference(true)}
            type="button"
          >
            Add {data.length ? "another" : "a"} reference
          </button>
        ) : null}
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
