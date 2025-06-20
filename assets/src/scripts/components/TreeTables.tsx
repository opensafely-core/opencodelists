import React from "react";
import { ButtonGroup } from "react-bootstrap";
import Hierarchy from "../_hierarchy";
import { PageData } from "../types";
import StatusToggle from "./StatusToggle";

function TreeNode({
  code,
  codeToTerm,
  codeToStatus,
  hierarchy,
  isEditable,
  updateStatus,
  visiblePaths,
}: {
  code: string;
  codeToStatus: PageData["codeToStatus"];
  codeToTerm: PageData["codeToTerm"];
  hierarchy: Hierarchy;
  isEditable: PageData["isEditable"];
  updateStatus: Function;
  visiblePaths: PageData["visiblePaths"];
}) {
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
                    codeToTerm={codeToTerm}
                    codeToStatus={codeToStatus}
                    hierarchy={hierarchy}
                    isEditable={isEditable}
                    updateStatus={updateStatus}
                    visiblePaths={visiblePaths}
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
  codeToStatus,
  codeToTerm,
  hierarchy,
  isEditable,
  treeTables,
  updateStatus,
  visiblePaths,
}: {
  allCodes: PageData["allCodes"];
  codeToStatus: PageData["codeToStatus"];
  codeToTerm: PageData["codeToTerm"];
  hierarchy: Hierarchy;
  isEditable: PageData["isEditable"];
  treeTables: PageData["treeTables"];
  updateStatus: Function;
  visiblePaths: PageData["visiblePaths"];
}) {
  return (
    <>
      {treeTables.map(([heading, ancestorCodes]) => (
        <div className="mb-2 pb-2 overflow-auto" key={heading}>
          <h5>{heading}</h5>
          <div className="builder__container">
            {ancestorCodes.map((ancestorCode) => (
              <ul key={ancestorCode} className="tree__list">
                <TreeNode
                  code={ancestorCode}
                  codeToTerm={codeToTerm}
                  codeToStatus={codeToStatus}
                  hierarchy={hierarchy}
                  isEditable={isEditable}
                  updateStatus={updateStatus}
                  visiblePaths={visiblePaths}
                />
              </ul>
            ))}
          </div>
        </div>
      ))}
    </>
  );
}

export default TreeTables;
