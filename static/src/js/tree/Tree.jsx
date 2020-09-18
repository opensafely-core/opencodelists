import React from "react";

import Code from "../Code";
import DescendantToggle from "../DescendantToggle";
import Pipes from "../Pipes";
import Term from "../Term";

class Tree extends React.Component {
  constructor(props) {
    super(props);

    // initialise state with {code: true, …} for every code on the page
    const codes = Array.from(props.hierarchy.nodes);
    this.state = Object.fromEntries(codes.map((node) => [node, true]));

    this.toggleVisibility = this.toggleVisibility.bind(this);
  }

  toggleVisibility(code) {
    this.setState((state) => ({ [code]: !state[code] }));
  }

  hasDescendants(code) {
    return this.props.hierarchy.getDescendants(code).length > 0;
  }

  isVisible(code) {
    return this.props.hierarchy
      .getAncestors(code)
      .every((ancestor) => this.state[ancestor]);
  }

  renderTerm(code, term) {
    const element = <Term term={term} />;

    const inDefinition = this.props.definitionCodes.includes(code);

    // conditionally wrap Term in an <href> element if there's a URL for it. We
    // only want to link to codes included in the codelist so some codes will
    // stay unlinked.
    if (code in this.props.codeToURL) {
      return (
        <a
          style={inDefinition ? { textDecoration: "underline" } : null}
          href={this.props.codeToURL[code]}
        >
          {element}
        </a>
      );
    } else {
      return element;
    }
  }

  render() {
    return (
      <div>
        {this.props.trees.map((tree, i) => (
          <div className="mb-4" key={i}>
            <h4>{tree.heading}</h4>

            {tree.rows.map((row, i) => (
              <div
                className={this.isVisible(row.code) ? "d-flex" : "d-none"}
                key={i}
                style={{ whiteSpace: "nowrap" }}
              >
                <Pipes pipes={row.pipes} />
                {this.hasDescendants(row.code) ? (
                  <DescendantToggle
                    code={row.code}
                    isExpanded={this.state[row.code]}
                    toggleVisibility={this.toggleVisibility}
                  />
                ) : null}
                {this.renderTerm(row.code, row.term)} <Code code={row.code} />
              </div>
            ))}
          </div>
        ))}
      </div>
    );
  }
}

export default Tree;
