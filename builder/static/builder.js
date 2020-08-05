"use strict";

const URL = JSON.parse(document.getElementById("url").textContent);
const TABLES = JSON.parse(document.getElementById("tables").textContent);
const ANCESTORS_MAP = JSON.parse(
  document.getElementById("ancestors-map").textContent
);
const DESCENDANTS_MAP = JSON.parse(
  document.getElementById("descendants-map").textContent
);
const IS_EDITABLE = JSON.parse(
  document.getElementById("isEditable").textContent
);

class CodelistBuilder extends React.Component {
  constructor(props) {
    super(props);
    this.state = { updateQueue: [], updating: false, isEditable: IS_EDITABLE };
    props.tables.forEach((table) =>
      table.rows.forEach((row) => {
        this.state["status-" + row.code] = row.status;
        this.state["expanded-" + row.code] = true;
      })
    );

    this.updateStatus = this.updateStatus.bind(this);
    this.toggleVisibility = this.toggleVisibility.bind(this);
  }

  updateStatus(code, status) {
    this.setState((state, props) => {
      let newState = {
        ["status-" + code]: status,
        updateQueue: state.updateQueue.concat([{ code: code, status: status }]),
      };

      const descendantStatus = { "+": "(+)", "-": "(-)" }[status];
      const conflictingStatus = { "+": "-", "-": "+" }[status];

      DESCENDANTS_MAP[code].forEach((descendantCode) => {
        // If this descendant has any ancestors who conflict with the code that
        // has just been clicked on, and which are not direct ancestors/descendants
        // of the code that has clicked on, then mark the descendant as requiring
        // resolution.
        if (
          ANCESTORS_MAP[descendantCode].some(
            (ancestorCode) =>
              state["status-" + ancestorCode] === conflictingStatus &&
              !this.isDirectlyRelated(code, ancestorCode)
          )
        ) {
          newState["status-" + descendantCode] = "!";
        } else {
          newState["status-" + descendantCode] = descendantStatus;
        }
      });

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
    fetch(URL, {
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
    this.props.tables.forEach((table) => {
      table.rows.forEach((row) => {
        counts[this.status(row.code)] += 1;
      });
    });
    counts["total"] = Object.values(counts).reduce((a, b) => a + b);
    return counts;
  }

  render() {
    return (
      <div>
        <Summary counts={this.counts()} />
        {this.props.tables.map((table) => (
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
    );
  }
}

function Button(props) {
  const colour = props.symbol === "+" ? "success" : "danger";
  let buttonClasses = ["btn"];
  if (props.status.includes(props.symbol)) {
    if (props.status === props.symbol) {
      buttonClasses.push(`btn-${colour}`);
    }
	  else {
      buttonClasses.push(`btn-outline-${colour}`);
	  }
  } else if (props.status === "?" || props.status === "!") {
    buttonClasses.push("btn-outline-info");
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
          {props.counts["+"] + props.counts["(+)"]} have been included in the
          codelist.
        </li>
      )}
      {props.counts["-"] > 0 && (
        <li>
          {props.counts["-"] + props.counts["(-)"]} have been excluded from the
          codelist.
        </li>
      )}
      {props.counts["?"] > 0 && <li>{props.counts["?"]} are unresolved.</li>}
      {props.counts["!"] > 0 && <li>{props.counts["!"]} are in conflict.</li>}
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
  <CodelistBuilder tables={TABLES} />,
  document.querySelector("#codelist-builder-container")
);
