import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import React, { useState } from "react";
import { postFetchWithOptions, readValueFromPage } from "../../_utils";
import type { IS_EDITABLE, METADATA, UPDATE_URL } from "../../types";

export default function MetadataForm({
  id,
  name,
}: {
  id: string;
  name: string;
}) {
  const isEditable: IS_EDITABLE = readValueFromPage("is-editable");
  const metadata: METADATA = readValueFromPage("metadata");
  const updateURL: UPDATE_URL = readValueFromPage("update-url");
  const fieldMetadata = metadata?.[id as keyof METADATA];

  const [isEditing, setIsEditing] = useState(false);

  const queryClient = useQueryClient();
  const { data } = useQuery({
    queryKey: ["metadata", id],
    initialData: fieldMetadata,
    queryFn: () => fieldMetadata,
  });

  const updateMetadata = useMutation({
    mutationFn: async (body: Record<string, unknown>) => {
      return postFetchWithOptions({
        body,
        url: updateURL,
      });
    },
    onSuccess: (data) => {
      queryClient.setQueryData(["metadata", id], data.metadata[id]);
      setIsEditing(false);
    },
  });

  if (!fieldMetadata) return null;

  function handleSubmit(event: React.FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const formData = new FormData(event.currentTarget);
    const formFieldData = Object.fromEntries(formData);
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
              // @ts-ignore: we're not currently using react-query to return
              // the expected values of the typescript compiler
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
          // @ts-ignore
        ) : data?.html ? (
          <div
            className="builder__markdown"
            // @ts-ignore: we're not currently using react-query to return
            // the expected values of the typescript compiler
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
