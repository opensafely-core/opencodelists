import React, { useEffect, useState } from "react";
import {
  Button,
  ButtonGroup,
  Form,
  Modal,
  OverlayTrigger,
  Tooltip,
} from "react-bootstrap";
import { getCookie } from "../_utils";

interface ManagementFormProps {
  counts: {
    "!": number;
    "(+)": number;
    "(-)": number;
    "+": number;
    "-": number;
    "?": number;
    total: number;
  };
}

export default function ManagementForm({ counts }: ManagementFormProps) {
  const [showDiscardModal, setShowDiscardModal] = useState(false);
  const [isComplete, setIsComplete] = useState(false);

  useEffect(
    function calculateCounts() {
      if (counts["!"] === 0 && counts["?"] === 0) {
        return setIsComplete(true);
      }
      return setIsComplete(false);
    },
    [counts],
  );

  return (
    <>
      <Form method="POST">
        <Form.Control
          id="csrfmiddlewaretoken"
          name="csrfmiddlewaretoken"
          type="hidden"
          value={getCookie("csrftoken")}
        />
        <Form.Control id="action" name="action" type="hidden" value="" />
        <ButtonGroup aria-label="Codelist actions" className="d-block" vertical>
          {isComplete ? (
            <Button
              block
              name="action"
              type="submit"
              value="save-for-review"
              variant="outline-primary"
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
                <Button block disabled variant="outline-secondary">
                  Save for review
                </Button>
              </OverlayTrigger>
            </>
          )}
          <Button
            block
            name="action"
            type="submit"
            value="save-draft"
            variant="outline-primary"
          >
            Save draft
          </Button>
          <Button
            block
            type="button"
            variant="outline-primary"
            onClick={() => setShowDiscardModal(true)}
          >
            Discard
          </Button>
        </ButtonGroup>
      </Form>
      <hr />
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
              variant="primary"
            >
              Yes
            </Button>
          </Form>
          <Button
            variant="secondary"
            onClick={() => setShowDiscardModal(false)}
          >
            No
          </Button>
        </Modal.Body>
      </Modal>
    </>
  );
}
