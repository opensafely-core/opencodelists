import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import React, { useState } from "react";
import { postFetchWithOptions, readValueFromPage } from "../../_utils";
import type { IS_EDITABLE, METADATA } from "../../types";

function Reference({
  isEditable,
  reference,
}: {
  isEditable: IS_EDITABLE;
  reference: METADATA["references"][number];
}) {
  const [isEditing, setIsEditing] = useState(false);

  const queryClient = useQueryClient();
  const addReference = useMutation({
    mutationFn: async (updatedReferences) => {
      return postFetchWithOptions({
        body: { references: updatedReferences },
        url: readValueFromPage("update-url"),
      });
    },
    onSuccess: (data) => {
      queryClient.setQueryData(["references"], data.metadata.references);
      setIsEditing(false);
    },
  });

  function handleSubmit(event: React.FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const currentReferences = queryClient.getQueryData(["references"]) as METADATA["references"];
    const filteredReferences = currentReferences.filter(
      (ref) => ref.url !== reference.url && ref.text !== reference.text,
    );
    const formData = new FormData(event.currentTarget);
    const formFieldData = Object.fromEntries(formData) as { text: string; url: string };
    const updatedReferences = [...filteredReferences, formFieldData];
    addReference.mutate(updatedReferences);
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
            <button className="btn btn-outline-danger ml-1" type="button">
              Delete
            </button>
          </div>
        )}
      </div>
      {isEditing && (
        <form
          className="border-top mt-2 pt-2"
          onReset={() => setIsEditing(false)}
          onSubmit={handleSubmit}
        >
          <div className="form-group">
            <label className="form-label" htmlFor="addReferenceText">
              Text
            </label>
            <input
              defaultValue={reference.text}
              placeholder="Text to display"
              required
              name="text"
              type="text"
              id="addReferenceText"
              className="form-control"
            />
          </div>
          <div className="form-group">
            <label className="form-label" htmlFor="addReferenceUrl">
              URL
            </label>
            <input
              defaultValue={reference.url}
              placeholder="Website to link to"
              required
              name="url"
              type="url"
              id="addReferenceUrl"
              className="form-control"
            />
          </div>
          <div className="btn-group-sm">
            <button type="submit" className="btn btn-primary">
              Save
            </button>
            <button type="reset" className="btn btn-secondary ml-1">
              Cancel
            </button>
          </div>
        </form>
      )}
    </li>
  );
}

export default function References() {
  const isEditable = readValueFromPage("is-editable");
  const { references }: METADATA = readValueFromPage("metadata");

  const [showAddReference, setShowAddReference] = useState(false);

  const queryClient = useQueryClient();
  const { data } = useQuery({
    queryKey: ["references"],
    initialData: references,
    queryFn: () => references,
  });

  const addReference = useMutation({
    mutationFn: async (updatedReferences) => {
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

  function handleSubmit(event: React.FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const currentReferences = queryClient.getQueryData(["references"]).data as METADATA["references"];
    const formData = new FormData(event.currentTarget);
    const formFieldData = Object.fromEntries(formData) as { text: string; url: string };
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
              <form
                onReset={() => setShowAddReference(false)}
                onSubmit={handleSubmit}
              >
                <div className="form-group">
                  <label className="form-label" htmlFor="addReferenceText">
                    Text
                  </label>
                  <input
                    placeholder="Text to display"
                    required
                    name="text"
                    type="text"
                    id="addReferenceText"
                    className="form-control"
                  />
                </div>
                <div className="form-group">
                  <label className="form-label" htmlFor="addReferenceUrl">
                    URL
                  </label>
                  <input
                    placeholder="Website to link to"
                    required
                    name="url"
                    type="url"
                    id="addReferenceUrl"
                    className="form-control"
                  />
                </div>
                <div className="btn-group-sm">
                  <button type="submit" className="btn btn-primary">
                    Save
                  </button>
                  <button type="reset" className="btn btn-secondary ml-1">
                    Cancel
                  </button>
                </div>
              </form>
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
