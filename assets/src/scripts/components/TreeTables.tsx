import React from "react";
import { TreeProps } from "./Tree";
import TreeTable from "./TreeTable";

export interface TreeTableProps extends TreeProps {
  treeTables: [string, string[]][];
  visiblePaths: Set<string>;
}

interface TreeTablesState {
  visiblePaths: Set<string>;
}

class TreeTables extends React.Component<TreeTableProps, TreeTablesState> {
  constructor(props: TreeTableProps) {
    super(props);
    this.state = { visiblePaths: props.visiblePaths };
    this.toggleVisibility = this.toggleVisibility.bind(this);
  }

  toggleVisibility(path: string) {
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
