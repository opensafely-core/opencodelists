import React from "react";
import { Form } from "react-bootstrap";
import type { Reference } from "../../types";

interface ReferenceFormProps {
  reference?: Reference;
  onCancel: () => void;
  onSave: (reference: Reference) => void;
}

/**
 * Form component for adding or editing reference links in a codelist's metadata.
 * @param reference - Optional existing reference to edit, or blank if creating a new one
 * @param onCancel - Callback when user cancels editing
 * @param onSave - Callback when user saves changes, receives updated reference object
 */
export default function ReferenceForm({
  reference = { text: "", url: "" },
  onCancel,
  onSave,
}: ReferenceFormProps) {
  const textInputRef = React.useRef<HTMLInputElement>(null);
  const urlInputRef = React.useRef<HTMLInputElement>(null);

  const handleSave = () => {
    onSave({
      text: textInputRef.current?.value || "",
      url: urlInputRef.current?.value || "",
    });
  };

  return (
    <div className="card p-3">
      <Form.Group className="mb-2">
        <Form.Label>Text</Form.Label>
        <Form.Control
          ref={textInputRef}
          type="text"
          defaultValue={reference.text}
          placeholder="Text to display"
        />
      </Form.Group>
      <Form.Group className="mb-3">
        <Form.Label>URL</Form.Label>
        <Form.Control
          ref={urlInputRef}
          type="url"
          defaultValue={reference.url}
          placeholder="URL to link to"
        />
      </Form.Group>
      <div className="mt-2 d-flex flex-row justify-content-end">
        <button
          type="button"
          className="btn btn-secondary btn-sm m-1"
          onClick={onCancel}
        >
          Cancel
        </button>
        <button
          type="button"
          className="btn btn-primary btn-sm m-1"
          onClick={handleSave}
        >
          Save
        </button>
      </div>
    </div>
  );
}
