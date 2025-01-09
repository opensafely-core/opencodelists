import PropTypes from "prop-types";
import React, { useState } from "react";
import { Button, ButtonGroup, Modal } from "react-bootstrap";
import { readValueFromPage } from "../_utils";
import DescendantToggle from "./DescendantToggle";
import MoreInfoModal from "./MoreInfoModal";
import Pipes from "./Pipes";
import StatusToggle from "./StatusToggle";

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
        <MoreInfoModal
          allCodes={allCodes}
          code={code}
          codeToStatus={codeToStatus}
          codeToTerm={codeToTerm}
          hierarchy={hierarchy}
          status={status}
          term={term}
        />
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
