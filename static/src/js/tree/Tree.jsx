import React from "react";
import TermAndCode from "../TermAndCode";

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
              >
                <TermAndCode
                  term={row.term}
                  code={row.code}
                  pipes={row.pipes}
                  hasDescendants={this.hasDescendants(row.code)}
                  isExpanded={this.state[row.code]}
                  toggleVisibility={this.toggleVisibility}
                />
              </div>
            ))}
          </div>
        ))}
      </div>
    );
  }
}

export default Tree;
