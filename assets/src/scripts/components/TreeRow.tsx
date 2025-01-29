import React from "react";
import { ButtonGroup } from "react-bootstrap";
import Hierarchy from "../_hierarchy";
import {
  Code,
  IsExpanded,
  PageData,
  Path,
  Pipe,
  Status,
  Term,
  ToggleVisibility,
} from "../types";
import DescendantToggle from "./DescendantToggle";
import MoreInfoModal from "./MoreInfoModal";
import Pipes from "./Pipes";
import StatusToggle from "./StatusToggle";

interface TreeRowProps {
  allCodes: PageData["allCodes"];
  code: Code;
  codeToStatus: PageData["codeToStatus"];
  codeToTerm: PageData["codeToTerm"];
  hasDescendants: boolean;
  hierarchy: Hierarchy;
  isEditable: PageData["isEditable"];
  isExpanded: IsExpanded;
  path: Path;
  pipes: Pipe[];
  status: Status;
  term: Term;
  toggleVisibility: ToggleVisibility;
  updateStatus: Function;
}

export default function TreeRow({
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
}: TreeRowProps) {
  const statusToColour = {
    "+": "text-body",
    "(+)": "text-body",
    "-": "text-secondary",
    "(-)": "text-secondary",
    "!": "text-danger",
    "?": "text-body",
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
