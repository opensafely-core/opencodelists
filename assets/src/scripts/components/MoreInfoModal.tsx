import React, { useEffect, useState } from "react";
import { Button, Modal } from "react-bootstrap";
import Hierarchy from "../_hierarchy";
import { Code, PageData, Status, Term } from "../types";

interface CreateModalTextProps {
  allCodes: PageData["allCodes"];
  code: Code;
  codeToStatus: PageData["codeToStatus"];
  codeToTerm: PageData["codeToTerm"];
  hierarchy: Hierarchy;
  status: Status;
}

function createModalText({
  allCodes,
  code,
  codeToStatus,
  codeToTerm,
  hierarchy,
  status,
}: CreateModalTextProps) {
  const included = allCodes.filter((c) => codeToStatus[c] === "+");
  const excluded = allCodes.filter((c) => codeToStatus[c] === "-");
  const significantAncestors = hierarchy.significantAncestors(
    code,
    included,
    excluded,
  );

  const includedAncestorsText = significantAncestors.includedAncestors
    .map((code: Code) => `${codeToTerm[code]} (${code})`)
    .join(", ");

  const excludedAncestorsText = significantAncestors.excludedAncestors
    .map((code: Code) => `${codeToTerm[code]} (${code})`)
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

interface MoreInfoModalProps {
  allCodes: PageData["allCodes"];
  code: Code;
  codeToStatus: PageData["codeToStatus"];
  codeToTerm: PageData["codeToTerm"];
  hierarchy: Hierarchy;
  status: Status;
  term: Term;
}

function MoreInfoModal({
  allCodes,
  code,
  codeToStatus,
  codeToTerm,
  hierarchy,
  status,
  term,
}: MoreInfoModalProps) {
  const [showMoreInfoModal, setShowMoreInfoModal] = useState(false);
  const [modalText, setModalText] = useState("");

  useEffect(() => {
    if (showMoreInfoModal) {
      setModalText(
        createModalText({
          allCodes,
          code,
          codeToStatus,
          codeToTerm,
          hierarchy,
          status,
        }),
      );
    }
  }, [showMoreInfoModal]);

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
        centered
        onHide={() => setShowMoreInfoModal(false)}
        show={showMoreInfoModal}
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
