import PropTypes from "prop-types";
import React from "react";
import TreeTable from "./TreeTable";

class TreeTables extends React.Component {
  constructor(props) {
    super(props);
    this.state = { visiblePaths: props.visiblePaths };
    this.toggleVisibility = this.toggleVisibility.bind(this);
  }

  toggleVisibility(path) {
    this.setState((state) => {
      const visiblePaths = new Set(state.visiblePaths);
      this.props.hierarchy.toggleVisibility(visiblePaths, path);
      return { visiblePaths: visiblePaths };
    });
  }

  render() {
    const {
      codeToStatus,
      codeToTerm,
      hierarchy,
      showMoreInfoModal,
      treeTables,
      updateStatus,
    } = this.props;

    return treeTables.map(([heading, ancestorCodes]) => (
      <TreeTable
        key={heading}
        ancestorCodes={ancestorCodes}
        codeToStatus={codeToStatus}
        codeToTerm={codeToTerm}
        heading={heading}
        hierarchy={hierarchy}
        showMoreInfoModal={showMoreInfoModal}
        toggleVisibility={this.toggleVisibility}
        updateStatus={updateStatus}
        visiblePaths={this.state.visiblePaths}
      />
    ));
  }
}

export default TreeTables;

TreeTables.propTypes = {
  codeToStatus: PropTypes.objectOf(PropTypes.string),
  codeToTerm: PropTypes.objectOf(PropTypes.string),
  hierarchy: PropTypes.shape({
    ancestorMap: PropTypes.shape(),
    childMap: PropTypes.objectOf(PropTypes.array),
    nodes: PropTypes.shape(),
    parentMap: PropTypes.objectOf(PropTypes.arrayOf(PropTypes.string)),
    toggleVisibility: PropTypes.func,
  }),
  showMoreInfoModal: PropTypes.func,
  treeTables: PropTypes.arrayOf(PropTypes.array),
  updateStatus: PropTypes.func,
  visiblePaths: PropTypes.objectOf(PropTypes.string),
};
