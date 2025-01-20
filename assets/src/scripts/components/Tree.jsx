import PropTypes from "prop-types";
import React from "react";
import TreeRow from "./TreeRow";

function Tree({
  allCodes,
  ancestorCode,
  codeToStatus,
  codeToTerm,
  hierarchy,
  isEditable,
  toggleVisibility,
  updateStatus,
  visiblePaths,
}) {
  return hierarchy
    .treeRows(ancestorCode, codeToStatus, codeToTerm, visiblePaths)
    .map((row) => (
      <TreeRow
        allCodes={allCodes}
        code={row.code}
        codeToStatus={codeToStatus}
        codeToTerm={codeToTerm}
        hasDescendants={row.hasDescendants}
        hierarchy={hierarchy}
        isEditable={isEditable}
        isExpanded={row.isExpanded}
        key={row.path}
        path={row.path}
        pipes={row.pipes}
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
  toggleVisibility: PropTypes.func,
  updateStatus: PropTypes.func,
  visiblePaths: PropTypes.shape(),
};
