import React, { useEffect, useState } from "react";
import { Modal, OverlayTrigger, Tooltip } from "react-bootstrap";
import { getCookie } from "../../_utils";
import type { SummaryProps } from "../Cards/Summary";

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
      <form method="POST" className="d-flex flex-row">
        <input
          className="form-control"
          id="csrfmiddlewaretoken"
          name="csrfmiddlewaretoken"
          type="hidden"
          value={getCookie("csrftoken")}
        />
        <input
          className="form-control"
          id="action"
          name="action"
          type="hidden"
          value=""
        />
        {isComplete ? (
          <button
            className="btn btn-outline-success"
            name="action"
            type="submit"
            value="save-for-review"
          >
            Save for review
          </button>
        ) : (
          <OverlayTrigger
            placement="right"
            overlay={
              <Tooltip id="disabled-review">
                You cannot save for review until all search results are included
                or excluded
              </Tooltip>
            }
          >
            <button
              className="btn btn-outline-secondary"
              disabled
              type="button"
            >
              Save for review
            </button>
          </OverlayTrigger>
        )}
        <button
          className="btn btn-outline-primary ml-2"
          name="action"
          type="submit"
          value="save-draft"
        >
          Save draft
        </button>
        <button
          className="btn btn-outline-danger ml-2"
          onClick={() => setShowDiscardModal(true)}
          type="button"
        >
          Discard
        </button>
      </form>

      <Modal centered show={showDiscardModal}>
        <div className="modal-header">
          Are you sure you want to discard this draft?
        </div>
        <div className="modal-body">
          <form className="d-inline" method="POST">
            <input
              className="form-control"
              id="csrfmiddlewaretoken"
              name="csrfmiddlewaretoken"
              type="hidden"
              value={getCookie("csrftoken")}
            />
            <input
              className="form-control"
              id="action"
              name="action"
              type="hidden"
              value="discard"
            />
            <button
              className="btn btn-danger mr-2"
              type="submit"
              value="discard"
            >
              Discard draft
            </button>
          </form>
          <button
            className="btn btn-outline-secondary"
            onClick={() => setShowDiscardModal(false)}
            type="button"
          >
            Continue editing
          </button>
        </div>
      </Modal>
    </>
  );
}
