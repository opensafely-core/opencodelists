import PropTypes from "prop-types";
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
  showMoreInfoModal: PropTypes.func,
  toggleVisibility: PropTypes.func,
  updateStatus: PropTypes.func,
  visiblePaths: PropTypes.shape(),
};
