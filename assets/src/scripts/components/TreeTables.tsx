import React from "react";
import { CodeToStatus } from "../types";
import { TreeProps } from "./Tree";
import TreeTable from "./TreeTable";

export interface TreeTablesProps {
  ancestorCodes?: TreeProps["ancestorCode"][];
  codeToStatus: CodeToStatus;
  codeToTerm: TreeProps["codeToTerm"];
  heading?: string;
  hierarchy: TreeProps["hierarchy"];
  showMoreInfoModal: TreeProps["showMoreInfoModal"];
  toggleVisibility: TreeProps["toggleVisibility"];
  treeTables: [string, string[]][];
  updateStatus: TreeProps["updateStatus"];
  visiblePaths: TreeProps["visiblePaths"];
}

interface ComponentState {
  visiblePaths: TreeProps["visiblePaths"];
}

class TreeTables extends React.Component<TreeTablesProps, ComponentState> {
  constructor(props: TreeTablesProps) {
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
