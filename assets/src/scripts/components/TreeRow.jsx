import PropTypes from "prop-types";
import React, { useState } from "react";
import { Button, ButtonGroup, Modal } from "react-bootstrap";
import { readValueFromPage } from "../_utils";
import DescendantToggle from "./DescendantToggle";
import Pipes from "./Pipes";
import StatusToggle from "./StatusToggle";

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

function TreeRow({
  allCodes,
  code,
  codeToStatus,
  codeToTerm,
  hasDescendants,
  hierarchy,
  isEditable,
  isExpanded,
  path,
  pipes,
  status,
  term,
  toggleVisibility,
  updateStatus,
}) {
  const statusToColour = {
    "+": "text-body",
    "(+)": "text-body",
    "-": "text-secondary",
    "(-)": "text-secondary",
    "!": "text-danger",
  };

  const rowSpacing = pipes.length === 0 ? "mt-2" : "mt-0";
  const className = `${rowSpacing} d-flex`;

  const modalText = isEditable
    ? createModalText({
        allCodes,
        code,
        codeToStatus,
        codeToTerm,
        hierarchy,
        status,
      })
    : "";
  const [showMoreInfoModal, setShowMoreInfoModal] = useState(false);

  return (
    <div className={className} data-code={code} data-path={path}>
      <ButtonGroup>
        <StatusToggle
          code={code}
          status={status}
          symbol="+"
          updateStatus={updateStatus}
        />
        <StatusToggle
          code={code}
          status={status}
          symbol="-"
          updateStatus={updateStatus}
        />
      </ButtonGroup>

      <div className="pl-2 whitespace-nowrap">
        <Pipes pipes={pipes} />
        {hasDescendants ? (
          <DescendantToggle
            isExpanded={isExpanded}
            path={path}
            toggleVisibility={toggleVisibility}
          />
        ) : null}
        <span className={statusToColour[status]}>{term}</span>
        <span className="ml-1">
          (<code>{code}</code>)
        </span>
      </div>

      {isEditable ? (
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
      ) : null}
    </div>
  );
}

export default TreeRow;

TreeRow.propTypes = {
  code: PropTypes.string,
  hasDescendants: PropTypes.bool,
  isExpanded: PropTypes.bool,
  path: PropTypes.string,
  pipes: PropTypes.arrayOf(PropTypes.string),
  showMoreInfoModal: PropTypes.func,
  status: PropTypes.string,
  term: PropTypes.string,
  toggleVisibility: PropTypes.func,
  updateStatus: PropTypes.func,
};
