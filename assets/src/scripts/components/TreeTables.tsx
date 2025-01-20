import React from "react";
import Hierarchy from "../_hierarchy";
import TreeTable from "./TreeTable";

interface TreeTablesProps {
  allCodes: string[];
  ancestorCodes?: string[];
  codeToStatus: { [key: string]: "+" | "(+)" | "-" | "(-)" | "!" | "?" };
  codeToTerm: {
    [key: string]: string;
  };
  hierarchy: Hierarchy;
  isEditable: boolean;
  toggleVisibility: (path: string) => void;
  treeTables: [string, string[]][];
  updateStatus: Function;
  visiblePaths: Set<string>;
}

export default class TreeTables extends React.Component<
  TreeTablesProps,
  { visiblePaths: Set<string> }
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
