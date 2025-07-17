import React, { useContext } from "react";
import {
  Code,
  IsExpanded,
  Path,
  Pipe,
  Status,
  Term,
  ToggleVisibility,
} from "../../types";
import { CodelistContext } from "../Layout/CodelistTab";
import DescendantToggle from "./DescendantToggle";
import MoreInfoModal from "./MoreInfoModal";
import Pipes from "./Pipes";
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
  const { isEditable } = useContext(CodelistContext);

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
        <MoreInfoModal code={code} status={status} term={term} />
      ) : null}
    </div>
  );
}
