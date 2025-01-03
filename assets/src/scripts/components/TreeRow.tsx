import React from "react";
import { ButtonGroup } from "react-bootstrap";
import { PipesState } from "../types";
import DescendantToggle from "./DescendantToggle";
import MoreInfoButton from "./MoreInfoButton";
import Pipes from "./Pipes";
import StatusToggle from "./StatusToggle";

export interface TreeRowProps {
  code: string;
  hasDescendants: boolean;
  isExpanded: boolean;
  path: string;
  pipes: PipesState;
  showMoreInfoModal: Function;
  status: string;
  term: string;
  toggleVisibility: Function;
  updateStatus: Function;
}

function TreeRow({
  code,
  hasDescendants,
  isExpanded,
  path,
  pipes,
  showMoreInfoModal,
  status,
  term,
  toggleVisibility,
  updateStatus,
}: TreeRowProps) {
  const statusToColour: { [key: string]: string } = {
    "+": "black",
    "(+)": "black",
    "-": "gray",
    "(-)": "gray",
    "!": "red",
  };

  const rowSpacing = pipes.length === 0 ? "mt-2" : "mt-0";
  const className = `${rowSpacing} d-flex`;

  return (
    <div className={className} data-code={code} data-path={path}>
      <ButtonGroup size="sm">
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

      <div className="pl-2" style={{ whiteSpace: "nowrap" }}>
        <Pipes pipes={pipes} />
        {hasDescendants ? (
          <DescendantToggle
            isExpanded={isExpanded}
            path={path}
            toggleVisibility={toggleVisibility}
          />
        ) : null}
        <span style={{ color: statusToColour[status] }}>{term}</span>
        <span className="ml-1">
          (<code>{code}</code>)
        </span>
      </div>

      {showMoreInfoModal && (
        <MoreInfoButton code={code} showMoreInfoModal={showMoreInfoModal} />
      )}
    </div>
  );
}

export default TreeRow;
