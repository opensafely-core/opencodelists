import React from "react";
import { Modal } from "react-bootstrap";

interface ReferenceFormProps {
  defaultValue?: {
    text: string;
    url: string;
  };
  onReset: React.FormEventHandler<HTMLFormElement>;
  onSubmit: React.FormEventHandler<HTMLFormElement>;
  show: boolean;
}

export default function ReferenceForm({
  defaultValue,
  onReset,
  onSubmit,
  show,
}: ReferenceFormProps) {
  return (
    <Modal
      animation={false}
      backdrop="static"
      show={show}
      size="lg"
      aria-labelledby="reference-edit-modal"
      centered
    >
      <form onReset={onReset} onSubmit={onSubmit}>
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
