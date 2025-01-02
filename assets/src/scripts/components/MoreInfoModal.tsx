import React from "react";
import { Modal } from "react-bootstrap";

interface MoreInfoModalProps {
  code: string;
  excludedAncestorsText: string;
  hideModal: Function;
  includedAncestorsText: string;
  status: string;
  term: string;
}

function MoreInfoModal({
  code,
  excludedAncestorsText,
  hideModal,
  includedAncestorsText,
  status,
  term,
}: MoreInfoModalProps) {
  let text = null;

  switch (status) {
    case "+":
      text = "Included";
      break;
    case "(+)":
      text = `Included by ${includedAncestorsText}`;
      break;
    case "-":
      text = "Excluded";
      break;
    case "(-)":
      text = `Excluded by ${includedAncestorsText}`;
      break;
    case "?":
      text = "Unresolved";
      break;
    case "!":
      text = `In conflict!  Included by ${includedAncestorsText}, and excluded by ${excludedAncestorsText}`;
      break;
  }

  return (
    <Modal centered onHide={() => hideModal} show={code !== null}>
      <Modal.Header closeButton>
        {term} ({code})
      </Modal.Header>
      <Modal.Body>{text}</Modal.Body>
    </Modal>
  );
}

export default MoreInfoModal;
