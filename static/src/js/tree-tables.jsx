"use strict";

import React from "react";

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
    const { hierarchy, treeTables, codeToStatus, codeToTerm } = this.props;

    return treeTables.map(([heading, ancestorCodes]) => (
      <TreeTable
        key={heading}
        hierarchy={hierarchy}
        heading={heading}
        ancestorCodes={ancestorCodes}
        codeToStatus={codeToStatus}
        codeToTerm={codeToTerm}
        visiblePaths={this.state.visiblePaths}
        toggleVisibility={this.toggleVisibility}
      />
    ));
  }
}

function TreeTable(props) {
  const {
    hierarchy,
    heading,
    ancestorCodes,
    codeToStatus,
    codeToTerm,
    visiblePaths,
    toggleVisibility,
  } = props;

  return (
    <div className="mb-4">
      <h4>{heading}</h4>

      {ancestorCodes.map((ancestorCode) => (
        <Tree
          key={ancestorCode}
          hierarchy={hierarchy}
          ancestorCode={ancestorCode}
          codeToStatus={codeToStatus}
          codeToTerm={codeToTerm}
          visiblePaths={visiblePaths}
          toggleVisibility={toggleVisibility}
        />
      ))}
    </div>
  );
}

function Tree(props) {
  const {
    hierarchy,
    ancestorCode,
    codeToStatus,
    codeToTerm,
    visiblePaths,
    toggleVisibility,
  } = props;

  return hierarchy
    .treeRows(ancestorCode, codeToStatus, codeToTerm, visiblePaths)
    .map((row) => (
      <TreeRow
        key={row.path}
        code={row.code}
        path={row.path}
        status={row.status}
        term={row.term}
        pipes={row.pipes}
        hasDescendants={row.hasDescendants}
        isExpanded={row.isExpanded}
        toggleVisibility={toggleVisibility}
      />
    ));
}

function TreeRow(props) {
  const {
    code,
    path,
    term,
    status,
    pipes,
    hasDescendants,
    isExpanded,
    toggleVisibility,
  } = props;

  const statusToColour = {
    "+": "black",
    "-": "gray",
  };

  return (
    <div className="d-flex" style={{ whiteSpace: "nowrap" }}>
      <Pipes pipes={pipes} />
      {hasDescendants ? (
        <DescendantToggle
          path={path}
          isExpanded={isExpanded}
          toggleVisibility={toggleVisibility}
        />
      ) : null}
      <span style={{ color: statusToColour[status] }}>{term}</span>
      <span className="ml-1">
        (<code>{code}</code>)
      </span>
    </div>
  );
}

function Pipes(props) {
  const { pipes } = props;
  return pipes.map((pipe, ix) => (
    <span
      key={ix}
      style={{
        display: "inline-block",
        textAlign: "center",
        paddingLeft: "3px",
        paddingRight: "6px",
        width: "20px",
      }}
    >
      {pipe}
    </span>
  ));
}

function DescendantToggle(props) {
  const { isExpanded, path } = props;

  return (
    <span
      onClick={props.toggleVisibility.bind(null, path)}
      style={{ cursor: "pointer", marginLeft: "2px", marginRight: "4px" }}
    >
      {" "}
      {isExpanded ? "⊟" : "⊞"}
    </span>
  );
}

export default TreeTables;
