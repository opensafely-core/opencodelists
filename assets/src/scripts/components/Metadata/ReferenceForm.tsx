import React from "react";
import { Form, Modal } from "react-bootstrap";
import { Reference } from "../../types";

interface ReferenceFormProps {
  reference?: Reference;
  onCancel: () => void;
  onSave: (reference: Reference) => void;
  show: boolean;
}

/**
 * Form component for adding or editing reference links in a codelist's metadata.
 * @param reference - Optional existing reference to edit, or blank if creating a new one
 * @param onCancel - Callback when user cancels editing
 * @param onSave - Callback when user saves changes, receives updated reference object
 * @param show - Controls visibility of the modal
 */
export default function ReferenceForm({
  reference = { text: "", url: "" },
  onCancel,
  onSave,
  show,
}: ReferenceFormProps) {
  const textInputRef = React.useRef<HTMLInputElement>(null);
  const urlInputRef = React.useRef<HTMLInputElement>(null);

  const handleSubmit = () => {
    onSave({
      text: textInputRef.current?.value || "",
      url: urlInputRef.current?.value || "",
    });
  };

  return (
    <Modal
      animation={false}
      show={show}
      onHide={onCancel}
      backdrop="static"
      aria-labelledby="reference-modal-title"
      centered
    >
      <Form onSubmit={handleSubmit}>
        <Modal.Header closeButton>
          <Modal.Title id="reference-modal-title">
            {reference.text ? "Edit Reference" : "Add Reference"}
          </Modal.Title>
        </Modal.Header>
        <Modal.Body>
          <Form.Group className="mb-2">
            <Form.Label>Text</Form.Label>
            <Form.Control
              ref={textInputRef}
              type="text"
              defaultValue={reference.text}
              placeholder="Text to display"
              required
            />
          </Form.Group>
          <Form.Group className="mb-3">
            <Form.Label>URL</Form.Label>
            <Form.Control
              ref={urlInputRef}
              type="url"
              defaultValue={reference.url}
              placeholder="URL to link to"
              required
            />
          </Form.Group>
        </Modal.Body>
        <Modal.Footer>
          <button
            type="button"
            className="btn btn-secondary btn-sm m-1"
            onClick={onCancel}
          >
            Cancel
          </button>
          <button type="submit" className="btn btn-primary btn-sm m-1">
            Save
          </button>
        </Modal.Footer>
      </Form>
    </Modal>
  );
}
