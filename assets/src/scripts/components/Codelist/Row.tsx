import React from "react";
import { ButtonGroup } from "react-bootstrap";
import type Hierarchy from "../../_hierarchy";
import type {
  Code,
  IsExpanded,
  PageData,
  Path,
  Pipe,
  Status,
  Term,
  ToggleVisibility,
} from "../../types";
import DescendantToggle from "./DescendantToggle";
import MoreInfoModal from "./MoreInfoModal";
import Pipes from "./Pipes";
import StatusToggle from "./StatusToggle";

interface RowProps {
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

export default function Row({
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
}: RowProps) {
  const statusTermColor = {
    "+": "text-body",
    "(+)": "text-body",
    "-": "text-secondary",
    "(-)": "text-secondary",
    "!": "text-danger",
    "?": "text-body",
  };

  const statusCodeColor = {
    "+": "",
    "(+)": "",
    "-": "text-secondary",
    "(-)": "text-secondary",
    "!": "text-danger",
    "?": "",
  };

  return (
    <div
      className={
        "builder__row" + (pipes.length === 0 ? " builder__row--mt" : "")
      }
      data-code={code}
      data-path={path}
    >
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
        <span className={statusTermColor[status]}>{term} </span>
        <code className={statusCodeColor[status]}>{code}</code>
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
