import PropTypes from "prop-types";
import React from "react";
import Tree from "./Tree";

function TreeTable({
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
}) {
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

export default TreeTable;

TreeTable.propTypes = {
  ancestorCodes: PropTypes.arrayOf(PropTypes.string),
  codeToStatus: PropTypes.objectOf(PropTypes.string),
  codeToTerm: PropTypes.objectOf(PropTypes.string),
  heading: PropTypes.string,
  hierarchy: PropTypes.shape({
    ancestorMap: PropTypes.shape(),
    childMap: PropTypes.objectOf(PropTypes.array),
    nodes: PropTypes.shape(),
    parentMap: PropTypes.objectOf(PropTypes.arrayOf(PropTypes.string)),
  }),
  toggleVisibility: PropTypes.func,
  updateStatus: PropTypes.func,
  visiblePaths: PropTypes.shape(),
};
