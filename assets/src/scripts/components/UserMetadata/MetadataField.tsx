import React, { useState } from "react";
import { Form } from "react-bootstrap";
import { getFetchOptions } from "../../_utils";

type MetadataFieldName = "description" | "methodology";

export default function MetadataField({ field, metadata, updateURL }) {
  const label = field.charAt(0).toUpperCase() + field.slice(1);
  const [htmlContent] = useState(metadata[field].html);
  const [isEditing, setIsEditing] = useState(metadata[field].isEditing);
  const [draftContent, setDraftContent] = useState(metadata[field].text);

  const handleSave = async (field: MetadataFieldName) => {
    const updateBody = {
      description:
        field === "description" ? draftContent : metadata.description.text,
      methodology:
        field === "methodology" ? draftContent : metadata.methodology.text,
    };
    const fetchOptions = getFetchOptions(updateBody);
    try {
      fetch(updateURL, fetchOptions)
        .then((response) => response.json())
        .then((data) => {
          // We rely on the backend rendering the html from the updated markdown
          // so we need to update the state here with the response from the server
          this.setState(() => ({ metadata: data.metadata }));
        });
    } catch (error) {
      console.error(`Failed to save ${field}:`, error);
    }
  };

  return (
    <Form.Group className={`card ${field}`} controlId={field}>
      <div className="card-body">
        <div className="card-title d-flex flex-row justify-content-between align-items-center">
          <Form.Label className="h5" as="h3">
            {label}
          </Form.Label>
          {isEditing ? (
            <div>
              <button
                type="button"
                className="btn btn-primary btn-sm"
                onClick={() => handleSave(field)}
                title={`Save ${field}`}
              >
                Save
              </button>
              <button
                type="button"
                className="btn btn-secondary btn-sm ml-2"
                onClick={() => setIsEditing(false)}
                title={`Cancel ${field} edit`}
              >
                Cancel
              </button>
            </div>
          ) : (
            <button
              type="button"
              className="btn btn-sm btn-warning"
              onClick={() => setIsEditing(true)}
              title={`Edit ${field}`}
            >
              Edit
            </button>
          )}
        </div>
        <hr />
        {isEditing ? (
          <>
            <Form.Control
              as="textarea"
              value={draftContent}
              onChange={(event) => {
                setDraftContent(event.target.value);
              }}
              rows={5}
              defaultValue={draftContent}
              autoFocus
              onKeyDown={(e) => {
                // Handle Ctrl+Enter for Save
                if (e.key === "Enter" && (e.ctrlKey || e.metaKey)) {
                  e.preventDefault();
                  //   this.handleSave(field);
                }
                // Handle Escape for Cancel
                if (e.key === "Escape") {
                  e.preventDefault();
                  setIsEditing(false);
                }
              }}
            />
            <Form.Text className="text-muted">
              If you make changes, please remember to click Save (shortcut:
              CTRL-ENTER) to keep them or Cancel (shortcut: ESC) to discard.
            </Form.Text>
          </>
        ) : (
          <>
            <style>{` .markdown p:last-child { margin-bottom: 0; } `}</style>
            <div
              className="markdown"
              dangerouslySetInnerHTML={{
                __html:
                  htmlContent ||
                  `<em class="text-muted">No ${field} provided yet</em>`,
              }}
            />
          </>
        )}
      </div>
    </Form.Group>
  );
}
