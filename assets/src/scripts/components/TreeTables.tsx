import React from "react";
import Hierarchy from "../_hierarchy";
import { PageData } from "../types";

interface TreeTablesProps {
  allCodes: PageData["allCodes"];
  ancestorCodes?: string[];
  codeToStatus: PageData["codeToStatus"];
  codeToTerm: PageData["codeToTerm"];
  hierarchy: Hierarchy;
  isEditable: PageData["isEditable"];
  treeTables: PageData["treeTables"];
  updateStatus: Function;
  visiblePaths: PageData["visiblePaths"];
}

function TreeNode({
  code,
  codeToTerm,
  codeToStatus,
  hierarchy,
  isEditable,
  updateStatus,
  visiblePaths
}) {
  const term = codeToTerm[code];
  const hasDescendants = !!hierarchy.childMap[code]?.length;

  return (
    <li className="tree__item" title={term} key={code}>
      {hasDescendants ? (
        <details open={visiblePaths?.has(code)}>
          <summary>
            {term} {code}
          </summary>
          <ul className="tree__list">
            {hierarchy.childMap[code].map((child) => (
              <TreeNode
                key={child}
                code={child}
                codeToTerm={codeToTerm}
                codeToStatus={codeToStatus}
                hierarchy={hierarchy}
                isEditable={isEditable}
                updateStatus={updateStatus}
              />
            ))}
          </ul>
        </details>
      ) : (
        <>
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
