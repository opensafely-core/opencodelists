import React from "react";
import { AncestorCodeType, TreePassProps } from "../types";
import TreeTable from "./TreeTable";

export interface TreeTablesProps extends TreePassProps {
  ancestorCodes?: AncestorCodeType[];
  treeTables: [string, string[]][];
}

interface ComponentState {
  visiblePaths: TreePassProps["visiblePaths"];
}

export default class TreeTables extends React.Component<
  TreeTablesProps,
  ComponentState
> {
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
      allCodes,
      codeToStatus,
      codeToTerm,
      hierarchy,
      isEditable,
      treeTables,
      updateStatus,
    } = this.props;

    return treeTables.map(([heading, ancestorCodes]) => (
      <TreeTable
        key={heading}
        allCodes={allCodes}
        ancestorCodes={ancestorCodes}
        codeToStatus={codeToStatus}
        codeToTerm={codeToTerm}
        heading={heading}
        hierarchy={hierarchy}
        isEditable={isEditable}
        toggleVisibility={this.toggleVisibility}
        updateStatus={updateStatus}
        visiblePaths={this.state.visiblePaths}
      />
    ));
  }
}
