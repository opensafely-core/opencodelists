import React from "react";
import { useCodelistContext } from "../../context/codelist-context";
import {
  Code,
  IsExpanded,
  Path,
  Pipe,
  Status,
  Term,
  ToggleVisibility,
} from "../../types";
import MoreInfoModal from "./MoreInfoModal";
import StatusToggle from "./StatusToggle";

interface RowProps {
  code: Code;
  hasDescendants: boolean;
  isExpanded: IsExpanded;
  path: Path;
  pipes: Pipe[];
  status: Status;
  term: Term;
  toggleVisibility: ToggleVisibility;
  updateStatus: Function;
}

export default function Row({
  code,
  hasDescendants,
  isExpanded,
  path,
  pipes,
  status,
  term,
  toggleVisibility,
  updateStatus,
}: RowProps) {
  const { isEditable } = useCodelistContext();

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
      <div className="btn-group" role="group">
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
      </div>

      <div className="pl-2 whitespace-nowrap">
        {pipes.map((pipe, ix) => (
          <span
            key={ix}
            className="d-inline-block pl-1 pr-2 text-center text-monospace"
          >
            {pipe}
          </span>
        ))}
        {hasDescendants ? (
          <button
            className="p-0 bg-transparent border-0 text-monospace d-inline-block ml-1 mr-2"
            onClick={toggleVisibility.bind(null, path)}
            type="button"
          >
            {" "}
            {isExpanded ? "⊟" : "⊞"}
          </button>
        ) : null}
        <span className={statusTermColor[status]}>{term} </span>
        <code className={statusCodeColor[status]}>{code}</code>
      </div>

      {isEditable ? (
        <MoreInfoModal code={code} status={status} term={term} />
      ) : null}
    </div>
  );
}
