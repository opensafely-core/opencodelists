import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import React, { useState } from "react";
import { postFetchWithOptions, readValueFromPage } from "../../_utils";

export default function MetadataForm({
  id,
  name,
}: {
  id: string;
  name: string;
}) {
  const isEditable = readValueFromPage("is-editable");
  const apiURLs = readValueFromPage("api-urls");

  const [isEditing, setIsEditing] = useState(false);

  const queryClient = useQueryClient();
  const { data, isPending, isError } = useQuery({
    queryKey: ["metadata", id],
    queryFn: async () => {
      const response = await fetch(
        apiURLs[id],
      );
      if (!response.ok) throw new Error("File list not found");
      return response.json();
    },
  });

  const updateMetadata = useMutation({
    mutationFn: async (body: Record<string, FormDataEntryValue>) => {
      return postFetchWithOptions({
        body,
        url: readValueFromPage("update-url"),
      });
    },
    onSuccess: (data) => {
      queryClient.setQueryData(["metadata", id], data.metadata[id]);
      setIsEditing(false);
    },
  });

  if (isPending || isError) {
    return (
      <div className="card">
        <div className="card-header d-flex flex-row align-items-center">
          <h3 className="h5 mb-0 mr-auto">{name}</h3>
        </div>

        <div className="card-body">
          {isPending && <p className="mb-0">{name} loading&hellip;</p>}
          {isError && (
            <p className="mb-0 text-danger font-weight-bold">
              {name} failed to load.
            </p>
          )}
        </div>
      </div>
    );
  }


  function handleSubmit(event: React.FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const formFieldData = Object.fromEntries(new FormData(event.currentTarget));
    updateMetadata.mutate(formFieldData);
  }

  function handleKeyDown(e: React.KeyboardEvent<HTMLTextAreaElement>) {
    // Handle Ctrl+Enter for Save
    if (e.key === "Enter" && (e.ctrlKey || e.metaKey)) {
      e.preventDefault();
      (e.currentTarget.form as HTMLFormElement)?.requestSubmit();
    }

    // Handle Escape for Cancel
    if (e.key === "Escape") {
      e.preventDefault();
      setIsEditing(false);
    }
  }

  return (
    <form
      className="card"
      onReset={() => setIsEditing(false)}
      onSubmit={handleSubmit}
    >
      <div className="card-header d-flex flex-row align-items-center">
        <h3 className="h5 mb-0 mr-auto">{name}</h3>
        {isEditable ? (
          isEditing ? (
            <>
              <button className="btn btn-primary btn-sm" type="submit">
                Save
              </button>
              <button className="btn btn-secondary btn-sm ml-1" type="reset">
                Cancel
              </button>
            </>
          ) : (
            <button
              className="btn btn-primary btn-sm"
              onClick={() => setIsEditing(true)}
              type="button"
            >
              Edit <span className="sr-only">{name}</span>
            </button>
          )
        ) : null}
      </div>

      <div className="card-body">
        {isEditing ? (
          <div className="form-group">
            <label className="form-label sr-only" htmlFor={`metadata-${id}`}>
              {name}
            </label>
            <textarea
              className="form-control"
              defaultValue={data.text}
              id={`metadata-${id}`}
              name={id}
              onKeyDown={handleKeyDown}
              rows={5}
            ></textarea>
            <small className="form-text text-muted">
              If you make changes, please remember to click Save (shortcut:
              CTRL-ENTER) to keep them or Cancel (shortcut: ESC) to discard.
            </small>
          </div>
        ) : data.html ? (
          <div
            className="builder__markdown"
            // biome-ignore lint/security/noDangerouslySetInnerHtml: backend is validating the markdown content
            dangerouslySetInnerHTML={{ __html: data.html }}
          />
        ) : (
          <p className="mb-0 text-muted font-italic">{name} not provided</p>
        )}
      </div>
    </form>
  );
}
