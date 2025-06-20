import React, { useContext } from "react";
import { ButtonGroup } from "react-bootstrap";
import { BuilderContext } from "../state/BuilderContext";
import { PageData } from "../types";
import StatusToggle from "./StatusToggle";

function TreeNode({
  code,
  updateStatus,
}: {
  code: string;
  updateStatus: Function;
}) {
  const { codeToStatus, codeToTerm, isEditable, hierarchy, visiblePaths } =
    useContext(BuilderContext);
  const status = codeToStatus[code];
  const term = codeToTerm[code];
  const hasDescendants = !!hierarchy.childMap[code]?.length;

  return (
    <li className="tree__item" title={term} key={code}>
      {hasDescendants ? (
        <>
          <ButtonGroup>
            <StatusToggle
              code={code}
              disabled={isEditable}
              status={status}
              symbol="+"
              updateStatus={updateStatus}
            />
            <StatusToggle
              code={code}
              disabled={isEditable}
              status={status}
              symbol="-"
              updateStatus={updateStatus}
            />
          </ButtonGroup>
          <details
            open={
              visiblePaths.has(code) ||
              Array.from(visiblePaths).some(
                (path) => path.split(":").pop() === code,
              )
            }
          >
            <summary>
              <dl className="d-inline-flex flex-row">
                <dt className="sr-only">Name:</dt>
                <dd>{term}</dd>
                <dt className="sr-only">Code:</dt>
                <dd>
                  <code>{code}</code>
                </dd>
              </dl>
            </summary>
            <ul className="tree__list">
              {hierarchy.childMap[code]
                .slice()
                .sort((a, b) => {
                  const termA = codeToTerm[a] || "";
                  const termB = codeToTerm[b] || "";
                  return termA.localeCompare(termB);
                })
                .map((child) => (
                  <TreeNode
                    key={child}
                    code={child}
                    updateStatus={updateStatus}
                  />
                ))}
            </ul>
          </details>
        </>
      ) : (
        <>
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
          {term} {code}
        </>
      )}
    </li>
  );
}

function TreeTables({
  treeTables,
  updateStatus,
}: {
  treeTables: PageData["treeTables"];
  updateStatus: Function;
}) {
  return (
    <>
      {treeTables.map(([heading, ancestorCodes]) => (
        <div className="mb-2 pb-2 overflow-auto" key={heading}>
          <h5>{heading}</h5>
          <div className="builder__container">
            {ancestorCodes.map((ancestorCode) => (
              <ul key={ancestorCode} className="tree__list">
                <TreeNode code={ancestorCode} updateStatus={updateStatus} />
              </ul>
            ))}
          </div>
        </div>
      ))}
    </>
  );
}

export default TreeTables;
