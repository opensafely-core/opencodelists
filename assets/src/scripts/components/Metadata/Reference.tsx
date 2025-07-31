import { useMutation, useQueryClient } from "@tanstack/react-query";
import React, { useState } from "react";
import { postFetchWithOptions, readValueFromPage } from "../../_utils";
import type { IS_EDITABLE, METADATA } from "../../types";
import ReferenceForm from "./ReferenceForm";

export default function Reference({
  isEditable,
  reference,
}: {
  isEditable: IS_EDITABLE;
  reference: METADATA["references"][number];
}) {
  const [isEditing, setIsEditing] = useState(false);
  const updateUrl = readValueFromPage("update-url");

  const queryClient = useQueryClient();
  const updateReferences = useMutation({
    mutationFn: async (updatedReferences: METADATA["references"]) => {
      return postFetchWithOptions({
        body: { references: updatedReferences },
        url: updateUrl,
      });
    },
    onSuccess: (data) => {
      queryClient.setQueryData(["references"], data.metadata.references);
      setIsEditing(false);
    },
  });

  function handleSubmit(event: React.FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const currentReferences = queryClient.getQueryData([
      "references",
    ]) as METADATA["references"];
    const filteredReferences = currentReferences.filter(
      (ref) => ref.url !== reference.url && ref.text !== reference.text,
    );
    const formData = new FormData(event.currentTarget);
    const formFieldData = Object.fromEntries(
      formData,
    ) as METADATA["references"][number];
    const updatedReferences = [...filteredReferences, formFieldData];
    updateReferences.mutate(updatedReferences);
  }

  function handleDelete() {
    const currentReferences = queryClient.getQueryData([
      "references",
    ]) as METADATA["references"];
    const filteredReferences = currentReferences.filter(
      (ref) => ref.url !== reference.url && ref.text !== reference.text,
    );
    updateReferences.mutate(filteredReferences);
  }

  return (
    <li className="list-group-item" key={reference.url}>
      <div className="d-flex flex-row align-items-center">
        <a
          href={reference.url}
          className="mr-1"
          target="_blank"
          rel="noopener noreferrer"
        >
          {reference.text}
        </a>
        {isEditable && (
          <div className="ml-auto btn-group-sm">
            <button
              className={`btn ${isEditing ? "btn-primary" : "btn-outline-primary"}`}
              onClick={() => setIsEditing(true)}
              type="button"
            >
              Edit
            </button>
            <button
              className="btn btn-outline-danger ml-1"
              onClick={handleDelete}
              type="button"
            >
              Delete
            </button>
          </div>
        )}
      </div>
      {isEditing && (
        <ReferenceForm
          defaultValue={reference}
          onReset={() => setIsEditing(false)}
          onSubmit={handleSubmit}
        />
      )}
    </li>
  );
}
