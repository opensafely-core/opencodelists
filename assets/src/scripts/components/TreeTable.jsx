import React from "react";
import Tree from "./Tree";

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
}) {
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
