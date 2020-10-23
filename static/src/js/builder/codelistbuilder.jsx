"use strict";

import React from "react";
import Modal from "react-bootstrap/Modal";

import TreeTables from "../tree-tables";
import { getCookie } from "../utils";

class CodelistBuilder extends React.Component {
  constructor(props) {
    super(props);

    this.state = {
      codeToStatus: props.codeToStatus,
      updateQueue: [],
      updating: false,
      moreInfoModalCode: null,
    };

    this.updateStatus = this.updateStatus.bind(this);
    this.toggleVisibility = this.toggleVisibility.bind(this);
    this.showMoreInfoModal = this.showMoreInfoModal.bind(this);
    this.hideMoreInfoModal = this.hideMoreInfoModal.bind(this);
    this.getStatus = this.getStatus.bind(this);
    this.getHasDescendants = this.getHasDescendants.bind(this);
    this.getIsExpanded = this.getIsExpanded.bind(this);
    this.getIsVisible = this.getIsVisible.bind(this);
  }

  componentDidMount() {
    // This is required for testing.  See other uses for _isMounted for explanation.
    this._isMounted = true;
  }

  componentWillUnmount() {
    this._isMounted = false;
  }

  updateStatus(code, status) {
    this.setState(({ codeToStatus, updateQueue }, { hierarchy }) => {
      const newCodeToStatus = hierarchy.updateCodeToStatus(
        codeToStatus,
        code,
        status
      );

      return {
        codeToStatus: newCodeToStatus,
        updateQueue: updateQueue.concat([[code, newCodeToStatus[code]]]),
      };
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
        if (!this._isMounted) {
          // In tests the compenent is unmounted, and this may happen before
          // the promise is resolved.  Calling setState on an unmounted
          // component is a no-op and may indicate a memory leak, so it triggers
          // a warning.  Exiting early here prevents that warning.
          return;
        }

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

  showMoreInfoModal(code) {
    this.setState({ moreInfoModalCode: code });
  }

  hideMoreInfoModal() {
    this.setState({ moreInfoModalCode: null });
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
    this.props.displayedCodes.forEach((code) => {
      const status = this.state.codeToStatus[code];
      if (["?", "!", "+", "(+)", "-", "(-)"].includes(status)) {
        counts[status] += 1;
        counts["total"] += 1;
      }
    });
    return counts;
  }

  render() {
    const moreInfoModal =
      this.state.moreInfoModalCode &&
      this.renderMoreInfoModal(this.state.moreInfoModalCode);

    return (
      <>
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
            <hr />

            <DownloadButton
              enabled={this.counts()["!"] === 0 && this.counts()["?"] === 0}
              url={this.props.downloadURL}
            >
              Download codelist
            </DownloadButton>
          </div>

          <div className="col-9 pl-5">
            <h3 className="mb-4">Results</h3>
            <TreeTables
              codeToStatus={this.state.codeToStatus}
              hierarchy={this.props.hierarchy}
              treeTables={this.props.treeTables}
              codeToTerm={this.props.codeToTerm}
              visiblePaths={this.props.visiblePaths}
              updateStatus={this.updateStatus}
              showMoreInfoModal={this.showMoreInfoModal}
            />
            ,
          </div>
        </div>

        {moreInfoModal}
      </>
    );
  }

  renderMoreInfoModal(code) {
    const included = this.props.displayedCodes.filter(
      (c) => this.getStatus(c) === "+"
    );
    const excluded = this.props.displayedCodes.filter(
      (c) => this.getStatus(c) === "-"
    );
    const significantAncestors = this.props.hierarchy.significantAncestors(
      code,
      included,
      excluded
    );

    return (
      <MoreInfoModal
        code={code}
        status={this.getStatus(code)}
        includedAncestors={significantAncestors.includedAncestors}
        excludedAncestors={significantAncestors.excludedAncestors}
        hideModal={this.hideMoreInfoModal}
      />
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

function MoreInfoModal(props) {
  const {
    code,
    status,
    includedAncestors,
    excludedAncestors,
    hideModal,
  } = props;

  let text = null;

  switch (status) {
    case "+":
      text = "Included";
      break;
    case "(+)":
      text = `Included by ${includedAncestors.join(", ")}`;
      break;
    case "-":
      text = "Excluded";
      break;
    case "(-)":
      text = `Excluded by ${excludedAncestors.join(", ")}`;
      break;
    case "?":
      text = "Unresolved";
      break;
    case "!":
      text = `In conflict!  Included by ${includedAncestors.join(
        ", "
      )} by and excluded by ${excludedAncestors.join(", ")}`;
      break;
  }

  return (
    <Modal show={code !== null} onHide={hideModal} centered>
      <Modal.Header closeButton>{code}</Modal.Header>
      <Modal.Body>{text}</Modal.Body>
    </Modal>
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

function DownloadButton(props) {
  if (props.enabled) {
    return (
      <a className="btn btn-primary" href={props.url}>
        {props.children}
      </a>
    );
  }

  // Button is disabled, tell the user why
  return (
    <>
      <p>
        Downloads are disabled until all conflicted or unresolved concepts are
        resolved.
      </p>
      <a className="disabled btn btn-secondary text-white">{props.children}</a>
    </>
  );
}

export { CodelistBuilder as default };
