import React, { useState } from "react";
import { Button, Card, Form } from "react-bootstrap";
import { getFetchOptions } from "../../_utils";
import { PageData, Reference } from "../../types";

export default function MetadataField({
  field,
  label,
  metadata,
  updateURL,
}: {
  field: "description" | "methodology";
  label: string;
  metadata: {
    description: {
      text: string;
      html: string;
      isEditing: boolean;
    };
    methodology: {
      text: string;
      html: string;
      isEditing: boolean;
    };
    references: Reference[];
  };
  updateURL: PageData["updateURL"];
}) {
  const [isEditing, setIsEditing] = useState(metadata[field].isEditing);

  const [draftContent, setDraftContent] = useState(metadata[field].text);
  const [lastSavedState, setLastSavedState] = useState({
    html: metadata[field].html,
    text: metadata[field].text,
  });

  async function handleSave() {
    const fetchOptions = getFetchOptions({
      [field]: draftContent,
    });
    try {
      fetch(updateURL, fetchOptions)
        .then((response) => response.json())
        .then((data) => {
          // We rely on the backend rendering the html from the updated markdown
          // so we need to update the state here with the response from the server
          setDraftContent(data.metadata[field].text);

          // Then we need to store the state for the HTML view and
          // cancel button
          setLastSavedState({
            html: data.metadata[field].html,
            text: data.metadata[field].text,
          });
          setIsEditing(false);
        });
    } catch (error) {
      console.error(`Failed to save ${field}:`, error);
    }
  }

  function handleCancel() {
    setDraftContent(lastSavedState.text);
    setIsEditing(false);
  }

  return (
    <Card as="form" className="mb-3">
      <Card.Header className="d-flex flex-row justify-content-between align-items-center">
        <h3 className="h5 mb-0">{label}</h3>
        {isEditing ? (
          <div>
            <Button onClick={handleSave} size="sm" variant="success">
              Save
            </Button>
            <Button
              className="ml-1"
              onClick={handleCancel}
              size="sm"
              variant="secondary"
            >
              Cancel
            </Button>
          </div>
        ) : (
          <Button
            onClick={() => setIsEditing(true)}
            size="sm"
            variant="primary"
          >
            Edit
          </Button>
        )}
      </Card.Header>
      <Card.Body>
        {isEditing ? (
          <>
            <Form.Label className="sr-only">{label}</Form.Label>
            <Form.Control
              as="textarea"
              value={draftContent}
              onChange={(event) => {
                setDraftContent(event.target.value);
              }}
              rows={5}
              autoFocus
              onKeyDown={(e) => {
                // Handle Ctrl+Enter for Save
                if (e.key === "Enter" && (e.ctrlKey || e.metaKey)) {
                  e.preventDefault();
                  handleSave();
                }
                // Handle Escape for Cancel
                if (e.key === "Escape") {
                  e.preventDefault();
                  handleCancel();
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
                  lastSavedState.html ||
                  `<em class="text-muted">No ${field} provided yet</em>`,
              }}
            />
          </>
        )}
      </Card.Body>
    </Card>
  );
}
