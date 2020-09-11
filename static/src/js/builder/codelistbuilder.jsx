"use strict";

import React from "react";

import TermAndCode from "../TermAndCode";
import { getCookie } from "../utils";

class CodelistBuilder extends React.Component {
  constructor(props) {
    super(props);

    this.codes = props.hierarchy.nodes;

    let state = { updateQueue: [], updating: false };

    this.codes.forEach((code) => {
      state["status-" + code] = props.codeToStatus[code];
      state["expanded-" + code] = true;
    });

    this.state = state;

    this.updateStatus = this.updateStatus.bind(this);
    this.toggleVisibility = this.toggleVisibility.bind(this);
    this.getStatus = this.getStatus.bind(this);
    this.getHasDescendants = this.getHasDescendants.bind(this);
    this.getIsExpanded = this.getIsExpanded.bind(this);
    this.getIsVisible = this.getIsVisible.bind(this);
  }

  updateStatus(code, status) {
    this.setState((state, props) => {
      let codeToStatus = {};
      this.codes.forEach((c) => (codeToStatus[c] = state["status-" + c]));

      const updates = props.hierarchy.updateCodeToStatus(
        codeToStatus,
        code,
        status
      );

      let newState = {};
      Object.keys(updates).forEach(
        (c) => (newState["status-" + c] = updates[c])
      );

      newState.updateQueue = state.updateQueue.concat([
        [code, newState["status-" + code]],
      ]);

      return newState;
    }, this.maybePostUpdates);
  }

  maybePostUpdates() {
    if (this.state.updating || !this.state.updateQueue.length) {
      return;
    }
    this.setState({ updating: true }, this.postUpdates);
  }

  postUpdates() {
    fetch(this.props.updateURL, {
      method: "POST",
      credentials: "include",
      mode: "same-origin",
      headers: {
        Accept: "application/json",
        "Content-Type": "application/json",
        "X-CSRFToken": getCookie("csrftoken"),
      },
      body: JSON.stringify({ updates: this.state.updateQueue }),
    })
      .then((response) => response.json())
      .then((data) => {
        const lastUpdates = data.updates;

        this.setState(
          (state) => {
            const newUpdateQueue = state.updateQueue.slice(lastUpdates.length);
            return { updating: false, updateQueue: newUpdateQueue };
          },

          this.maybePostUpdates
        );
      });
  }

  toggleVisibility(code) {
    this.setState((state) => ({
      ["expanded-" + code]: !state["expanded-" + code],
    }));
  }

  getStatus(code) {
    return this.state["status-" + code];
  }

  getIsVisible(code) {
    return this.props.hierarchy
      .getAncestors(code)
      .every((ancestor) => this.getIsExpanded(ancestor));
  }

  getIsExpanded(code) {
    return this.state["expanded-" + code];
  }

  getHasDescendants(code) {
    return this.props.hierarchy.getDescendants(code).length > 0;
  }

  counts() {
    let counts = {
      "?": 0,
      "!": 0,
      "+": 0,
      "(+)": 0,
      "-": 0,
      "(-)": 0,
      total: 0,
    };
    this.codes.forEach((code) => {
      const status = this.getStatus(code);
      if (["?", "!", "+", "(+)", "-", "(-)"].includes(status)) {
        counts[status] += 1;
        counts["total"] += 1;
      }
    });
    return counts;
  }

  render() {
    return (
      <div className="row">
        <div className="col-3">
          <h3 className="mb-4">Summary</h3>
          <Filter filter={this.props.filter} />
          <Summary counts={this.counts()} />
          <hr />

          <h3 className="mb-4">Term searches</h3>
          <ul className="list-group">
            {this.props.searches.map((search) => (
              <TermSearch key={search.url} search={search} />
            ))}
          </ul>
          <hr />

          <h3 className="mb-4">New term search</h3>
          <SearchForm searchURL={this.props.searchURL} />
        </div>

        <div className="col-9 pl-5">
          <h3 className="mb-4">Results</h3>
          {this.props.tables.map((table) => (
            <Table
              key={table.heading}
              table={table}
              getStatus={this.getStatus}
              getHasDescendants={this.getHasDescendants}
              getIsVisible={this.getIsVisible}
              getIsExpanded={this.getIsExpanded}
              isEditable={this.props.isEditable}
              updateStatus={this.updateStatus}
              toggleVisibility={this.toggleVisibility}
            />
          ))}
        </div>
      </div>
    );
  }
}

function Filter(props) {
  const { filter } = props;
  return filter ? (
    <p>Filtered to {filter} concepts and their descendants.</p>
  ) : null;
}

function TermSearch(props) {
  const { search } = props;

  return (
    <a
      href={search.url}
      className={
        search.active
          ? "list-group-item list-group-item-action active"
          : "list-group-item list-group-item-action"
      }
    >
      {search.term}
    </a>
  );
}

function SearchForm(props) {
  const { searchURL } = props;

  return (
    <form method="post" action={searchURL}>
      <div className="form-group">
        <input
          type="hidden"
          name="csrfmiddlewaretoken"
          value={getCookie("csrftoken")}
        />
        <input
          type="search"
          className="form-control"
          name="term"
          placeholder="Search term"
        />
      </div>
      <button type="submit" name="search" className="btn btn-primary">
        Search
      </button>
    </form>
  );
}

function Table(props) {
  const {
    table,
    getStatus,
    getHasDescendants,
    getIsVisible,
    getIsExpanded,
    isEditable,
    updateStatus,
    toggleVisibility,
  } = props;

  return (
    <div className="mb-4">
      <h4>{table.heading}</h4>
      {table.rows.map((row, ix) => (
        <Row
          key={ix}
          row={row}
          status={getStatus(row.code)}
          hasDescendants={getHasDescendants(row.code)}
          isVisible={getIsVisible(row.code)}
          isExpanded={getIsExpanded(row.code)}
          isEditable={isEditable}
          updateStatus={updateStatus}
          toggleVisibility={toggleVisibility}
        />
      ))}
    </div>
  );
}

function Row(props) {
  const {
    row,
    status,
    hasDescendants,
    isVisible,
    isExpanded,
    isEditable,
    updateStatus,
    toggleVisibility,
  } = props;

  const visibility = isVisible ? "d-flex" : "d-none";
  const rowSpacing = row.pipes.length === 0 ? "mt-2" : "mt-0";
  const className = `${rowSpacing} ${visibility}`;

  return (
    <div className={className}>
      <div className="btn-group btn-group-sm" role="group">
        <Button
          code={row.code}
          symbol="+"
          status={status}
          isEditable={isEditable}
          updateStatus={updateStatus}
        />
        <Button
          code={row.code}
          symbol="-"
          status={status}
          isEditable={isEditable}
          updateStatus={updateStatus}
        />
      </div>

      <MoreInfo status={status} />

      <TermAndCode
        term={row.term}
        code={row.code}
        pipes={row.pipes}
        status={status}
        hasDescendants={hasDescendants}
        isExpanded={isExpanded}
        toggleVisibility={toggleVisibility}
      />
    </div>
  );
}

function Button(props) {
  const { code, symbol, status, isEditable, updateStatus } = props;

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
      onClick={isEditable && updateStatus.bind(null, code, symbol)}
      className={buttonClasses.join(" ")}
    >
      {symbol}
    </button>
  );
}

function MoreInfo(props) {
  const { status } = props;
  let text = null;

  switch (status) {
    case "+":
      text = "Included";
      break;
    case "(+)":
      text = "Included by ancestor";
      break;
    case "-":
      text = "Excluded";
      break;
    case "(-)":
      text = "Excluded by ancestor";
      break;
    case "?":
      text = "Unresolved";
      break;
    case "!":
      text = "In conflict";
      break;
  }

  return (
    <div className="btn-group btn-group-sm mx-2" role="group">
      <button
        type="button"
        data-toggle="tooltip"
        data-placement="top"
        title={text}
        className="btn btn-outline-secondary py-0"
      >
        ?
      </button>
    </div>
  );
}

function Summary(props) {
  return (
    <ul>
      <li>
        Found <span id="summary-total">{props.counts.total}</span> active
        matching concepts (including descendants).
      </li>
      {props.counts["+"] > 0 && (
        <li>
          <span id="summary-included">
            {props.counts["+"] + props.counts["(+)"]}
          </span>{" "}
          have been <a href="?filter=included">included</a> in the codelist.
        </li>
      )}
      {props.counts["-"] > 0 && (
        <li>
          <span id="summary-excluded">
            {props.counts["-"] + props.counts["(-)"]}
          </span>{" "}
          have been <a href="?filter=excluded">excluded</a> from the codelist.
        </li>
      )}
      {props.counts["?"] > 0 && (
        <li>
          <span id="summary-unresolved">{props.counts["?"]}</span> are{" "}
          <a href="?filter=unresolved">unresolved</a>.
        </li>
      )}
      {props.counts["!"] > 0 && (
        <li>
          <span id="summary-in-conflict">{props.counts["!"]}</span> are{" "}
          <a href="?filter=in-conflict">in conflict</a>.
        </li>
      )}
    </ul>
  );
}

export { CodelistBuilder as default };
