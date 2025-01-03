import React from "react";
import Tree, { TreeProps } from "./Tree";
import { CodeToStatus } from "../types";

interface TreeTableProps {
  ancestorCodes: TreeProps["ancestorCode"][];
  codeToStatus: CodeToStatus;
  codeToTerm: TreeProps["codeToTerm"];
  heading: string;
  hierarchy: TreeProps["hierarchy"];
  showMoreInfoModal: TreeProps["showMoreInfoModal"];
  toggleVisibility: TreeProps["toggleVisibility"];
  updateStatus: TreeProps["updateStatus"];
  visiblePaths: TreeProps["visiblePaths"];
}

function TreeTable({
  ancestorCodes,
  codeToStatus,
  codeToTerm,
  heading,
  hierarchy,
  showMoreInfoModal,
  toggleVisibility,
  updateStatus,
  visiblePaths,
}: TreeTableProps) {
  return (
    <div className="mb-4">
      <h5>{heading}</h5>

      {ancestorCodes.map((ancestorCode) => (
        <Tree
          key={ancestorCode}
          ancestorCode={ancestorCode}
          codeToStatus={codeToStatus}
          codeToTerm={codeToTerm}
          hierarchy={hierarchy}
          showMoreInfoModal={showMoreInfoModal}
          toggleVisibility={toggleVisibility}
          updateStatus={updateStatus}
          visiblePaths={visiblePaths}
        />
      ))}
    </div>
  );
}

export default TreeTable;
