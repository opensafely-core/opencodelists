"use strict";

// These could/should be passed to CodelistBuilder as props
const SEARCHES = JSON.parse(document.getElementById("searches").textContent);
const FILTER = JSON.parse(document.getElementById("filter").textContent);
const CODE_TO_STATUS = JSON.parse(
  document.getElementById("code-to-status").textContent
);
const TABLES = JSON.parse(document.getElementById("tables").textContent);
const ANCESTORS_MAP = JSON.parse(
  document.getElementById("ancestors-map").textContent
);
const DESCENDANTS_MAP = JSON.parse(
  document.getElementById("descendants-map").textContent
);
const CODES = Object.keys(ANCESTORS_MAP);
const IS_EDITABLE = JSON.parse(
  document.getElementById("isEditable").textContent
);
const UPDATE_URL = JSON.parse(
  document.getElementById("update-url").textContent
);
const SEARCH_URL = JSON.parse(
  document.getElementById("search-url").textContent
);

class CodelistBuilder extends React.Component {
  constructor(props) {
    super(props);

    this.state = { updateQueue: [], updating: false, isEditable: IS_EDITABLE };

    TABLES.forEach((table) =>
      table.rows.forEach((row) => {
        this.state["status-" + row.code] = row.status;
      })
    );

    CODES.forEach((code) => {
      this.state["status-" + code] = CODE_TO_STATUS[code];
      this.state["expanded-" + code] = true;
    });

    this.updateStatus = this.updateStatus.bind(this);
    this.toggleVisibility = this.toggleVisibility.bind(this);
  }

  updateStatus(code, status) {
    this.setState((state, props) => {
      let included = CODES.filter(
        (c) => state["status-" + c] === "+" && c !== code
      );
      let excluded = CODES.filter(
        (c) => state["status-" + c] === "-" && c !== code
      );

      if (status === "+" && state["status-" + code] !== "+") {
        included.push(code);
      } else if (status === "-" && state["status-" + code] !== "-") {
        excluded.push(code);
      }

      included = new Set(included);
      excluded = new Set(excluded);
      console.log(included);
      console.log(excluded);

      function newStatus(code) {
        // This function duplicates the logic of codelists.tree_utils.render

        if (included.has(code)) {
          // this node is explicitly included
          return "+";
        }
        if (excluded.has(code)) {
          // this node is explicitly excluded
          return "-";
        }

        // these are the ancestors of the node
        const ancestors = ANCESTORS_MAP[code];

        // these are the ancestors of the node that are directly included or excluded
        const includedOrExcludedAncestors = ancestors.filter(
          (a) => included.has(a) || excluded.has(a)
        );

        // these are the ancestors of the node that are directly included or excluded,
        // and which are not overridden by any of their descendants
        const significantIncludedOrExcludedAncestors = includedOrExcludedAncestors.filter(
          (a) =>
            !DESCENDANTS_MAP[a].some((d) =>
              includedOrExcludedAncestors.includes(d)
            )
        );

        // these are the significant included ancestors of the node
        const includedAncestors = significantIncludedOrExcludedAncestors.filter(
          (a) => included.has(a)
        );

        // these are the significant excluded ancestors of the node
        const excludedAncestors = significantIncludedOrExcludedAncestors.filter(
          (a) => excluded.has(a)
        );

        if (includedAncestors.length === 0 && excludedAncestors.length === 0) {
          // no ancestors are included or excluded, so this node is neither excluded or
          // excluded
          return "?";
        }

        if (includedAncestors.length > 0 && excludedAncestors.length === 0) {
          // some ancestors are included and none are excluded, so this node is included
          return "(+)";
        }

        if (excludedAncestors.length > 0 && includedAncestors.length === 0) {
          // some ancestors are excluded and none are included, so this node is excluded
          return "(-)";
        }

        // some ancestors are included and some are excluded, and neither set of
        // ancestors overrides the other
        return "!";
      }

      let newState = {};
      CODES.forEach((c) => (newState["status-" + c] = newStatus(c)));
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
    fetch(UPDATE_URL, {
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

  status(code) {
    return this.state["status-" + code];
  }

  isDirectlyRelated(code1, code2) {
    return (
      code1 === code2 ||
      DESCENDANTS_MAP[code2].includes(code1) ||
      DESCENDANTS_MAP[code1].includes(code2)
    );
  }

  isVisible(code) {
    return ANCESTORS_MAP[code].every((ancestor) => this.isExpanded(ancestor));
  }

  isExpanded(code) {
    return this.state["expanded-" + code];
  }

  termStyle(code) {
    return {
      color: {
        "!": "red",
        "-": "gray",
        "(-)": "gray",
      }[this.status(code)],
    };
  }

  counts() {
    let counts = { "?": 0, "!": 0, "+": 0, "(+)": 0, "-": 0, "(-)": 0 };
    CODES.forEach((code) => {
      counts[this.status(code)] += 1;
    });
    counts["total"] = Object.values(counts).reduce((a, b) => a + b);
    return counts;
  }

  render() {
    return (
      <div className="row">
        <div className="col-3">
          <h3 className="mb-4">Summary</h3>
          {FILTER ? (
            <p>Filtered to {FILTER} concepts and their descendants.</p>
          ) : null}
          <Summary counts={this.counts()} />
          <hr />
          <h3 className="mb-4">Term searches</h3>
          <ul className="list-group">
            {SEARCHES.map((search) => (
              <a
                key={search.url}
                href={search.url}
                className={
                  search.active
                    ? "list-group-item list-group-item-action active"
                    : "list-group-item list-group-item-action"
                }
              >
                {search.term}
              </a>
            ))}
          </ul>
          <hr />
          <h3 className="mb-4">New term search</h3>
          <form method="post" action={SEARCH_URL}>
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
        </div>

        <div className="col-9 pl-5">
          <h3 className="mb-4">Results</h3>
          {TABLES.map((table) => (
            <div key={table.heading} className="mb-4">
              <h4>{table.heading}</h4>
              {table.rows.map((row, ix) => (
                <div
                  className="row"
                  key={ix}
                  style={{
                    display: this.isVisible(row.code) ? "flex" : "none",
                  }}
                >
                  <div className="btn-group btn-group-sm" role="group">
                    <Button
                      code={row.code}
                      symbol="+"
                      status={this.status(row.code)}
                      isEditable={this.state.isEditable}
                      handleClick={this.updateStatus}
                    />
                    <Button
                      code={row.code}
                      symbol="-"
                      status={this.status(row.code)}
                      isEditable={this.state.isEditable}
                      handleClick={this.updateStatus}
                    />
                  </div>
                  <div style={{ paddingLeft: row.indent + "em" }}>
                    {DESCENDANTS_MAP[row.code].length ? (
                      <span
                        onClick={this.toggleVisibility.bind(null, row.code)}
                        style={{ cursor: "pointer" }}
                      >
                        {this.isExpanded(row.code) ? "⊟" : "⊞"}
                      </span>
                    ) : null}
                    <span style={this.termStyle(row.code)}>{row.term}</span>
                    &nbsp;
                    <span>
                      (<code>{row.code}</code>)
                    </span>
                  </div>
                </div>
              ))}
            </div>
          ))}
        </div>
      </div>
    );
  }
}

function Button(props) {
  let buttonClasses = ["btn"];
  if (props.status === props.symbol) {
    buttonClasses.push("btn-primary");
  } else if (props.status === `(${props.symbol})`) {
    buttonClasses.push("btn-secondary");
  } else {
    buttonClasses.push("btn-outline-secondary");
  }

  buttonClasses.push("py-0");

  return (
    <button
      type="button"
      onClick={
        props.isEditable &&
        props.handleClick.bind(null, props.code, props.symbol)
      }
      className={buttonClasses.join(" ")}
    >
      {props.symbol}
    </button>
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

ReactDOM.render(
  <CodelistBuilder />,
  document.querySelector("#codelist-builder-container")
);
