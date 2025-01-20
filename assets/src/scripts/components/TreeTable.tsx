import React from "react";
import Hierarchy from "../_hierarchy";
import Tree from "./Tree";

interface TreeTableProps {
  allCodes: string[];
  ancestorCodes: string[];
  codeToStatus: { [key: string]: "+" | "(+)" | "-" | "(-)" | "!" | "?" };
  codeToTerm: {
    [key: string]: string;
  };
  heading: string;
  hierarchy: Hierarchy;
  isEditable: boolean;
  toggleVisibility: (path: string) => void;
  updateStatus: Function;
  visiblePaths: Set<string>;
}

export default function TreeTable({
  allCodes,
  ancestorCodes,
  codeToStatus,
  codeToTerm,
  heading,
  hierarchy,
  isEditable,
  toggleVisibility,
  updateStatus,
  visiblePaths,
}: TreeTableProps) {
  return (
    <div className="mb-4">
      <h5>{heading}</h5>

      {ancestorCodes.map((ancestorCode) => (
        <Tree
          allCodes={allCodes}
          ancestorCode={ancestorCode}
          codeToStatus={codeToStatus}
          codeToTerm={codeToTerm}
          hierarchy={hierarchy}
          isEditable={isEditable}
          key={ancestorCode}
          toggleVisibility={toggleVisibility}
          updateStatus={updateStatus}
          visiblePaths={visiblePaths}
        />
      ))}
    </div>
  );
}
