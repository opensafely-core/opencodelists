"use strict";

import Button from "react-bootstrap/Button";
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

  shouldComponentUpdate(nextProps) {
    // Clicking an include or exclude button triggers three re-renders.  For large
    // codelists, this wastes a lot of time.  We can avoid this by only rending a
    // TreeTables component if any code's status has changed, or if a code has changed
    // visibility.

    const { codeToStatus, visiblePaths } = this.props;

    if (
      Object.keys(codeToStatus).some(
        (code) => codeToStatus[code] !== nextProps.codeToStatus[code]
      )
    ) {
      // If any code's status has changed, we should re-render the tree
      return true;
    }

    if (
      [...visiblePaths].some((path) => {
        !nextProps.visiblePaths.has(path);
      })
    ) {
      // If any code is now not visible, we should re-render the tree
      return true;
    }

    if (
      [...nextProps.visiblePaths].some((path) => {
        !visiblePaths.has(path);
      })
    ) {
      // If any code is now visible, we should re-render the tree
      return true;
    }

    return false;
  }

  render() {
    const {
      hierarchy,
      treeTables,
      codeToStatus,
      codeToTerm,
      updateStatus,
      showMoreInfoModal,
    } = this.props;

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
        updateStatus={updateStatus}
        showMoreInfoModal={showMoreInfoModal}
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
    updateStatus,
    showMoreInfoModal,
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
          updateStatus={updateStatus}
          showMoreInfoModal={showMoreInfoModal}
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
    updateStatus,
    showMoreInfoModal,
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
        updateStatus={updateStatus}
        showMoreInfoModal={showMoreInfoModal}
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
    updateStatus,
    showMoreInfoModal,
  } = props;

  const statusToColour = {
    "+": "black",
    "(+)": "black",
    "-": "gray",
    "(-)": "gray",
    "!": "red",
  };

  const rowSpacing = pipes.length === 0 ? "mt-2" : "mt-0";
  const className = `${rowSpacing} d-flex`;

  return (
    <div className={className} data-code={code} data-path={path}>
      <div className="btn-group btn-group-sm" role="group">
        <StatusToggle
          code={code}
          symbol="+"
          status={status}
          updateStatus={updateStatus}
        />
        <StatusToggle
          code={code}
          symbol="-"
          status={status}
          updateStatus={updateStatus}
        />
      </div>

      <div className="pl-2" style={{ whiteSpace: "nowrap" }}>
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

      {showMoreInfoModal && (
        <MoreInfoButton code={code} showMoreInfoModal={showMoreInfoModal} />
      )}
    </div>
  );
}

function StatusToggle(props) {
  const { code, symbol, status, updateStatus } = props;

  let buttonClasses = ["btn"];
  if (status === symbol) {
    buttonClasses.push("btn-primary");
  } else if (status === `(${symbol})`) {
    buttonClasses.push("btn-secondary");
  } else {
    buttonClasses.push("btn-outline-secondary");
  }
  buttonClasses.push("py-0");
  return (
    <button
      type="button"
      onClick={updateStatus && updateStatus.bind(null, code, symbol)}
      className={buttonClasses.join(" ")}
      data-symbol={symbol}
    >
      {symbol}
    </button>
  );
}

function MoreInfoButton(props) {
  const { code, showMoreInfoModal } = props;
  return (
    <div className="btn-group btn-group-sm mx-2" role="group">
      <Button
        variant="outline-secondary"
        onClick={showMoreInfoModal.bind(null, code)}
        className="py-0 border-0"
      >
        ...
      </Button>
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
