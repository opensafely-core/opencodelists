"use strict";

import React from "react";
import ReactDOM from "react-dom";

class CodelistBuilder extends React.Component {
  constructor(props) {
    super(props);

    this.state = { updateQueue: [], updating: false };

    this.codes = props.hierarchy.nodes;
    this.codes.forEach((code) => {
      this.state["status-" + code] = props.codeToStatus[code];
      this.state["expanded-" + code] = true;
    });

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
          (state, props) => {
            const newUpdateQueue = state.updateQueue.slice(lastUpdates.length);
            return { updating: false, updateQueue: newUpdateQueue };
          },

          this.maybePostUpdates
        );
      });
  }

  toggleVisibility(code) {
    this.setState((state, props) => ({
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
    let counts = { "?": 0, "!": 0, "+": 0, "(+)": 0, "-": 0, "(-)": 0 };
    this.codes.forEach((code) => {
      counts[this.getStatus(code)] += 1;
    });
    counts["total"] = Object.values(counts).reduce((a, b) => a + b);
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
    ix,
    status,
    hasDescendants,
    isVisible,
    isExpanded,
    isEditable,
    updateStatus,
    toggleVisibility,
  } = props;

  const style = { display: isVisible ? "flex" : "none" };
  const className = row.pipes.length === 0 ? "mt-2" : "mt-0";

  return (
    <div className="row" style={style} className={className}>
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

function TermAndCode(props) {
  const {
    term,
    code,
    pipes,
    status,
    hasDescendants,
    isExpanded,
    toggleVisibility,
  } = props;

  const termStyle = {
    color: {
      "!": "red",
      "-": "gray",
      "(-)": "gray",
    }[status],
  };

  return (
    <div style={{ paddingLeft: "10px", whiteSpace: "nowrap" }}>
      {pipes.map((pipe, ix) => (
        <span
          key={ix}
          style={{
            display: "inline-block",
            textAlign: "center",
            width: "20px",
          }}
        >
          {pipe}
        </span>
      ))}
      {hasDescendants ? (
        <span
          onClick={toggleVisibility.bind(null, code)}
          style={{ cursor: "pointer" }}
        >
          {isExpanded ? "⊟" : "⊞"}
        </span>
      ) : null}
      <span style={termStyle}>{term}</span>{" "}
      <span>
        (<code>{code}</code>)
      </span>
    </div>
  );
}

function Summary(props) {
  return (
    <ul>
      <li>
        Found {props.counts.total} active matching concepts (including
        descendants).
      </li>
      {props.counts["+"] > 0 && (
        <li>
          {props.counts["+"] + props.counts["(+)"]} have been{" "}
          <a href="?filter=included">included</a> in the codelist.
        </li>
      )}
      {props.counts["-"] > 0 && (
        <li>
          {props.counts["-"] + props.counts["(-)"]} have been{" "}
          <a href="?filter=excluded">excluded</a> from the codelist.
        </li>
      )}
      {props.counts["?"] > 0 && (
        <li>
          {props.counts["?"]} are <a href="?filter=unresolved">unresolved</a>.
        </li>
      )}
      {props.counts["!"] > 0 && (
        <li>
          {props.counts["!"]} are <a href="?filter=in-conflict">in conflict</a>.
        </li>
      )}
    </ul>
  );
}

// From https://docs.djangoproject.com/en/3.0/ref/csrf/
function getCookie(name) {
  let cookieValue = null;
  if (document.cookie && document.cookie !== "") {
    const cookies = document.cookie.split(";");
    for (let i = 0; i < cookies.length; i++) {
      const cookie = cookies[i].trim();
      // Does this cookie string begin with the name we want?
      if (cookie.substring(0, name.length + 1) === name + "=") {
        cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
        break;
      }
    }
  }
  return cookieValue;
}

function readValueFromPage(id) {
  return JSON.parse(document.getElementById(id).textContent);
}

class Hierarchy {
  constructor(parentMap, childMap) {
    this.nodes = Object.keys(parentMap);
    this.parentMap = parentMap;
    this.childMap = childMap;
    this.ancestorMap = {};
    this.descendantMap = {};
  }

  getAncestors(node) {
    if (!this.ancestorMap.hasOwnProperty(node)) {
      let ancestors = [];
      for (let parent of this.parentMap[node]) {
        ancestors.push(parent);
        for (let ancestor of this.getAncestors(parent)) {
          ancestors.push(ancestor);
        }
      }

      this.ancestorMap[node] = ancestors;
    }

    return this.ancestorMap[node];
  }

  getDescendants(node) {
    if (!this.descendantMap.hasOwnProperty(node)) {
      let descendants = [];
      for (let child of this.childMap[node]) {
        descendants.push(child);
        for (let descendant of this.getDescendants(child)) {
          descendants.push(descendant);
        }
      }

      this.descendantMap[node] = descendants;
    }

    return this.descendantMap[node];
  }

  updateCodeToStatus(codeToStatus, code, status) {
    let included = Object.keys(codeToStatus).filter(
      (c) => codeToStatus[c] === "+" && c !== code
    );
    let excluded = Object.keys(codeToStatus).filter(
      (c) => codeToStatus[c] === "-" && c !== code
    );

    if (status === "+" && codeToStatus[code] !== "+") {
      included.push(code);
    } else if (status === "-" && codeToStatus[code] !== "-") {
      excluded.push(code);
    }

    let updates = { [code]: this.codeStatus(code, included, excluded) };
    for (let descendant of this.getDescendants(code)) {
      updates[descendant] = this.codeStatus(descendant, included, excluded);
    }

    return updates;
  }

  codeStatus(code, included, excluded) {
    if (included.includes(code)) {
      // this code is explicitly included
      return "+";
    }
    if (excluded.includes(code)) {
      // this code is explicitly excluded
      return "-";
    }

    // these are the ancestors of the code
    const ancestors = this.getAncestors(code);

    // these are the ancestors of the code that are directly included or excluded
    const includedOrExcludedAncestors = ancestors.filter(
      (a) => included.includes(a) || excluded.includes(a)
    );

    if (includedOrExcludedAncestors.length === 0) {
      // no ancestors are included or excluded, so this code is neither excluded or
      // excluded
      return "?";
    }

    // these are the ancestors of the code that are directly included or excluded,
    // and which are not overridden by any of their descendants
    const significantIncludedOrExcludedAncestors = includedOrExcludedAncestors.filter(
      (a) =>
        !this.getDescendants(a).some((d) =>
          includedOrExcludedAncestors.includes(d)
        )
    );

    // these are the significant included ancestors of the code
    const includedAncestors = significantIncludedOrExcludedAncestors.filter(
      (a) => included.includes(a)
    );

    // these are the significant excluded ancestors of the code
    const excludedAncestors = significantIncludedOrExcludedAncestors.filter(
      (a) => excluded.includes(a)
    );

    if (includedAncestors.length > 0 && excludedAncestors.length === 0) {
      // some ancestors are included and none are excluded, so this code is included
      return "(+)";
    }

    if (excludedAncestors.length > 0 && includedAncestors.length === 0) {
      // some ancestors are excluded and none are included, so this code is excluded
      return "(-)";
    }

    // some ancestors are included and some are excluded, and neither set of
    // ancestors overrides the other
    return "!";
  }
}

// Next on my list is learning how to write tests properly!

function testUpdateCodeToStatus() {
  console.log("testUpdateCodeToStatus");
  const hierarchy = buildTestHierarchy();
  const codeToStatus = {
    //        ?
    //       / \
    //      +   -
    //     / \ / \
    //   (+)  !  (-)
    //   / \ / \ / \
    // (+)  !   !  (-)
    a: "?",
    b: "+",
    c: "-",
    d: "(+)",
    e: "!",
    f: "(-)",
    g: "(+)",
    h: "!",
    i: "!",
    j: "(-)",
  };

  const updates = hierarchy.updateCodeToStatus(codeToStatus, "c", "-");
  const expected = {
    //        ?
    //       / \
    //      +   ?
    //     / \ / \
    //   (+) (+)  ?
    //   / \ / \ / \
    // (+) (+) (+)  ?
    c: "?",
    e: "(+)",
    f: "?",
    h: "(+)",
    i: "(+)",
    j: "?",
  };

  if (checkEqual(updates, expected)) {
    console.log("passed");
  } else {
    console.log("failed");
    alert("testUpdateCodeToStatus failed");
  }
}

function testNodeToStatus() {
  function subTest(ix, included, excluded, expected) {
    console.log(`testNodeToStatus ${ix}`);
    const hierarchy = buildTestHierarchy();

    let codeToStatus = {};
    hierarchy.nodes.forEach((node) => {
      codeToStatus[node] = hierarchy.codeStatus(node, included, excluded);
    });

    if (checkEqual(codeToStatus, expected)) {
      console.log("passed");
    } else {
      console.log("failed");
      alert(`testNodeToStatus ${ix} failed`);
    }
  }

  subTest(1, [], [], {
    //        ?
    //       / \
    //      ?   ?
    //     / \ / \
    //    ?   ?   ?
    //   / \ / \ / \
    //  ?   ?   ?   ?
    a: "?",
    b: "?",
    c: "?",
    d: "?",
    e: "?",
    f: "?",
    g: "?",
    h: "?",
    i: "?",
    j: "?",
  });

  subTest(2, ["a"], [], {
    //        +
    //       / \
    //     (+) (+)
    //     / \ / \
    //   (+) (+) (+)
    //   / \ / \ / \
    // (+) (+) (+) (+)
    a: "+",
    b: "(+)",
    c: "(+)",
    d: "(+)",
    e: "(+)",
    f: "(+)",
    g: "(+)",
    h: "(+)",
    i: "(+)",
    j: "(+)",
  });

  subTest(3, ["b"], ["c"], {
    //        ?
    //       / \
    //      +   -
    //     / \ / \
    //   (+)  !  (-)
    //   / \ / \ / \
    // (+)  !   !  (-)
    a: "?",
    b: "+",
    c: "-",
    d: "(+)",
    e: "!",
    f: "(-)",
    g: "(+)",
    h: "!",
    i: "!",
    j: "(-)",
  });

  subTest(4, ["a", "b"], [], {
    //        +
    //       / \
    //      +  (+)
    //     / \ / \
    //   (+) (+) (+)
    //   / \ / \ / \
    // (+) (+) (+) (+)
    a: "+",
    b: "+",
    c: "(+)",
    d: "(+)",
    e: "(+)",
    f: "(+)",
    g: "(+)",
    h: "(+)",
    i: "(+)",
    j: "(+)",
  });

  subTest(5, ["a"], ["b"], {
    //        +
    //       / \
    //      -  (+)
    //     / \ / \
    //   (-) (-) (+)
    //   / \ / \ / \
    // (-) (-) (-) (+)
    a: "+",
    b: "-",
    c: "(+)",
    d: "(-)",
    e: "(-)",
    f: "(+)",
    g: "(-)",
    h: "(-)",
    i: "(-)",
    j: "(+)",
  });

  subTest(6, ["a"], ["b", "c"], {
    //        +
    //       / \
    //      -   -
    //     / \ / \
    //   (-) (-) (-)
    //   / \ / \ / \
    // (-) (-) (-) (-)
    a: "+",
    b: "-",
    c: "-",
    d: "(-)",
    e: "(-)",
    f: "(-)",
    g: "(-)",
    h: "(-)",
    i: "(-)",
    j: "(-)",
  });

  subTest(7, ["a", "e"], ["b", "c"], {
    //        +
    //       / \
    //      -   -
    //     / \ / \
    //   (-)  +  (-)
    //   / \ / \ / \
    // (-) (+) (+) (-)
    a: "+",
    b: "-",
    c: "-",
    d: "(-)",
    e: "+",
    f: "(-)",
    g: "(-)",
    h: "(+)",
    i: "(+)",
    j: "(-)",
  });
}

function buildTestHierarchy() {
  const parentMap = {
    a: [],
    b: ["a"],
    c: ["a"],
    d: ["b"],
    e: ["b", "c"],
    f: ["c"],
    g: ["d"],
    h: ["d", "e"],
    i: ["e", "f"],
    j: ["f"],
  };
  const childMap = {
    a: ["b", "c"],
    b: ["d", "e"],
    c: ["e", "f"],
    d: ["g", "h"],
    e: ["h", "i"],
    f: ["i", "j"],
    g: [],
    h: [],
    i: [],
    j: [],
  };

  return new Hierarchy(parentMap, childMap);
}

function checkEqual(actual, expected) {
  const differences = ["a", "b", "c", "d", "e", "f", "g", "h", "i"].filter(
    (c) => actual[c] != expected[c]
  );

  if (differences.length) {
    differences.forEach((c) => {
      console.log(c, actual[c], expected[c]);
    });

    return false;
  } else {
    return true;
  }
}

testNodeToStatus();
testUpdateCodeToStatus();

const hierarchy = new Hierarchy(
  readValueFromPage("parent-map"),
  readValueFromPage("child-map")
);

ReactDOM.render(
  <CodelistBuilder
    searches={readValueFromPage("searches")}
    filter={readValueFromPage("filter")}
    codeToStatus={readValueFromPage("code-to-status")}
    tables={readValueFromPage("tables")}
    isEditable={readValueFromPage("isEditable")}
    updateURL={readValueFromPage("update-url")}
    searchURL={readValueFromPage("search-url")}
    hierarchy={hierarchy}
  />,
  document.querySelector("#codelist-builder-container")
);
