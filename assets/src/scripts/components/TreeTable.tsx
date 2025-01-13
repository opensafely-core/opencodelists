import React from "react";
import { AncestorCodeType, TreePassProps } from "../types";
import Tree from "./Tree";

interface TreeTableProps extends TreePassProps {
  ancestorCodes: AncestorCodeType[];
  heading: string;
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
