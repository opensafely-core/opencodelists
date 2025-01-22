import React from "react";
import Hierarchy from "../_hierarchy";
import { PageData, Path, ToggleVisibility } from "../types";
import TreeTable from "./TreeTable";

interface TreeTablesProps {
  allCodes: PageData["allCodes"];
  ancestorCodes?: string[];
  codeToStatus: PageData["codeToStatus"];
  codeToTerm: PageData["codeToTerm"];
  hierarchy: Hierarchy;
  isEditable: PageData["isEditable"];
  toggleVisibility: ToggleVisibility;
  treeTables: PageData["treeTables"];
  updateStatus: Function;
  visiblePaths: PageData["visiblePaths"];
}

export default class TreeTables extends React.Component<
  TreeTablesProps,
  { visiblePaths: PageData["visiblePaths"] }
> {
  constructor(props: TreeTablesProps) {
    super(props);
    this.state = { visiblePaths: props.visiblePaths };
    this.toggleVisibility = this.toggleVisibility.bind(this);
  }

  toggleVisibility(path: Path) {
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
