import PropTypes from "prop-types";
import React from "react";
import TreeRow from "./TreeRow";

function Tree({
  ancestorCode,
  codeToStatus,
  codeToTerm,
  hierarchy,
  showMoreInfoModal,
  toggleVisibility,
  updateStatus,
  visiblePaths,
}) {
  return hierarchy
    .treeRows(ancestorCode, codeToStatus, codeToTerm, visiblePaths)
    .map((row) => (
      <TreeRow
        key={row.path}
        code={row.code}
        hasDescendants={row.hasDescendants}
        isExpanded={row.isExpanded}
        path={row.path}
        pipes={row.pipes}
        showMoreInfoModal={showMoreInfoModal}
        status={row.status}
        term={row.term}
        toggleVisibility={toggleVisibility}
        updateStatus={updateStatus}
      />
    ));
}

export default Tree;

Tree.propTypes = {
  ancestorCode: PropTypes.string,
  codeToStatus: PropTypes.objectOf(PropTypes.string),
  codeToTerm: PropTypes.objectOf(PropTypes.string),
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
