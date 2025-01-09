import React, { useState } from "react";
import { Button, Modal } from "react-bootstrap";

function createModalText({
  allCodes,
  code,
  codeToStatus,
  codeToTerm,
  hierarchy,
  status,
}) {
  const included = allCodes.filter((c) => codeToStatus[c] === "+");
  const excluded = allCodes.filter((c) => codeToStatus[c] === "-");
  const significantAncestors = hierarchy.significantAncestors(
    code,
    included,
    excluded,
  );

  const includedAncestorsText = significantAncestors.includedAncestors
    .map((code) => `${codeToTerm[code]} (${code})`)
    .join(", ");

  const excludedAncestorsText = significantAncestors.excludedAncestors
    .map((code) => `${codeToTerm[code]} (${code})`)
    .join(", ");

  let text = "";

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
      text = `Excluded by ${excludedAncestorsText}`;
      break;
    case "?":
      text = "Unresolved";
      break;
    case "!":
      text = `In conflict!  Included by ${includedAncestorsText}, and excluded by ${excludedAncestorsText}`;
      break;
  }

  return text;
}

function MoreInfoModal({
  allCodes,
  code,
  codeToStatus,
  codeToTerm,
  hierarchy,
  status,
  term,
}) {
  const [showMoreInfoModal, setShowMoreInfoModal] = useState(false);

  const modalText = createModalText({
    allCodes,
    code,
    codeToStatus,
    codeToTerm,
    hierarchy,
    status,
  });

  return (
    <>
      <Button
        className="py-0 border-0"
        onClick={() => setShowMoreInfoModal(true)}
        variant="outline-secondary"
      >
        &hellip;
      </Button>

      <Modal
        show={showMoreInfoModal}
        onHide={() => setShowMoreInfoModal(false)}
      >
        <Modal.Header closeButton>
          <Modal.Title>
            {term} ({code})
          </Modal.Title>
        </Modal.Header>
        <Modal.Body>{modalText}</Modal.Body>
      </Modal>
    </>
  );
}

export default MoreInfoModal;
