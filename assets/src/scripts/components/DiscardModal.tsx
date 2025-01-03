import React from "react";
import { Button, Form, Modal } from "react-bootstrap";
import { getCookie } from "../_utils";

function DiscardModal({
  show,
  handleCancel,
}: {
  show: boolean;
  handleCancel: () => void;
}) {
  return (
    <Modal centered show={show}>
      <Modal.Header>Are you sure you want to discard this draft?</Modal.Header>
      <Modal.Body>
        <Form className="d-inline" method="POST">
          <Form.Control
            id="csrfmiddlewaretoken"
            name="csrfmiddlewaretoken"
            type="hidden"
            value={getCookie("csrftoken")}
          />
          <Form.Control
            id="action"
            name="action"
            type="hidden"
            value="discard"
          />
          <Button
            className="mr-2"
            type="submit"
            value="discard"
            variant="primary"
          >
            Yes
          </Button>
        </Form>
        <Button variant="secondary" onClick={handleCancel}>
          No
        </Button>
      </Modal.Body>
    </Modal>
  );
}

export default DiscardModal;
