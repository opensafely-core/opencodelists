import React from "react";
import { Modal } from "react-bootstrap";

interface ReferenceFormModalProps {
  defaultValue?: {
    text: string;
    url: string;
  };
  onReset: React.FormEventHandler<HTMLFormElement>;
  onSubmit: React.FormEventHandler<HTMLFormElement>;
  show: boolean;
}

export default function ReferenceFormModal({
  defaultValue,
  onReset,
  onSubmit,
  show,
}: ReferenceFormModalProps) {
  function handleKeyDown(e: React.KeyboardEvent<HTMLFormElement>) {
    // Handle Escape for Cancel
    if (e.key === "Escape") {
      e.preventDefault();
      onReset(e);
    }
  }

  return (
    <Modal
      animation={false}
      backdrop="static"
      show={show}
      size="lg"
      aria-labelledby="reference-edit-modal"
      centered
    >
      <form onKeyDown={handleKeyDown} onReset={onReset} onSubmit={onSubmit}>
        <Modal.Header>
          <Modal.Title id="reference-edit-modal">
            {defaultValue ? "Edit Reference" : "Add Reference"}
          </Modal.Title>
        </Modal.Header>
        <Modal.Body>
          <div className="form-group">
            <label className="form-label" htmlFor="addReferenceText">
              Text
            </label>
            <input
              // biome-ignore lint/a11y/noAutofocus: It's fine to use this in a modal dialog
              autoFocus
              className="form-control"
              defaultValue={defaultValue?.text}
              id="addReferenceText"
              name="text"
              placeholder="Text to display"
              required
              type="text"
            />
          </div>
          <div className="form-group">
            <label className="form-label" htmlFor="addReferenceUrl">
              URL
            </label>
            <input
              className="form-control"
              defaultValue={defaultValue?.url}
              id="addReferenceUrl"
              name="url"
              placeholder="Website to link to"
              required
              type="url"
            />
          </div>
          <small className="form-text text-muted">
            Keyboard shortcuts: Save (ENTER) / Cancel (ESC)
          </small>
        </Modal.Body>
        <Modal.Footer>
          <div className="btn-group-sm">
            <button
              type="submit"
              className="plausible-event-name=Metadata+save+references btn btn-primary"
            >
              Save
            </button>
            <button type="reset" className="btn btn-secondary ml-1">
              Cancel
            </button>
          </div>
        </Modal.Footer>
      </form>
    </Modal>
  );
}
