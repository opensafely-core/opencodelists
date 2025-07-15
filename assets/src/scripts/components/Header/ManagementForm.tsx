import React, { useEffect, useState } from "react";
import { Button, Form, Modal, OverlayTrigger, Tooltip } from "react-bootstrap";
import { getCookie } from "../../_utils";
import { SummaryProps } from "../Cards/Summary";

interface ManagementFormProps {
  counts: SummaryProps["counts"];
}

export default function ManagementForm({ counts }: ManagementFormProps) {
  const [showDiscardModal, setShowDiscardModal] = useState(false);
  const [isComplete, setIsComplete] = useState(false);

  useEffect(
    function calculateCounts() {
      if (counts.total > 0 && counts["!"] === 0 && counts["?"] === 0) {
        return setIsComplete(true);
      }
      return setIsComplete(false);
    },
    [counts],
  );

  return (
    <>
      <Form method="POST" className="d-flex flex-row">
        <Form.Control
          id="csrfmiddlewaretoken"
          name="csrfmiddlewaretoken"
          type="hidden"
          value={getCookie("csrftoken")}
        />
        <Form.Control id="action" name="action" type="hidden" value="" />
        {isComplete ? (
          <Button
            name="action"
            type="submit"
            value="save-for-review"
            variant="outline-success"
          >
            Save for review
          </Button>
        ) : (
          <>
            <OverlayTrigger
              placement="right"
              overlay={
                <Tooltip id="disabled-review">
                  You cannot save for review until all search results are
                  included or excluded
                </Tooltip>
              }
            >
              <Button disabled variant="outline-secondary">
                Save for review
              </Button>
            </OverlayTrigger>
          </>
        )}
        <Button
          className="ml-2"
          name="action"
          type="submit"
          value="save-draft"
          variant="outline-primary"
        >
          Save draft
        </Button>
        <Button
          className="ml-2"
          onClick={() => setShowDiscardModal(true)}
          type="button"
          variant="outline-danger"
        >
          Discard
        </Button>
      </Form>

      <Modal centered show={showDiscardModal}>
        <Modal.Header>
          Are you sure you want to discard this draft?
        </Modal.Header>
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
              variant="danger"
            >
              Discard draft
            </Button>
          </Form>
          <Button
            variant="outline-secondary"
            onClick={() => setShowDiscardModal(false)}
          >
            Continue editing
          </Button>
        </Modal.Body>
      </Modal>
    </>
  );
}
