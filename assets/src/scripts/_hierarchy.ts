class Hierarchy {
  ancestorMap: Record<string, string[]>;
  childMap: Record<string, string[]>;
  descendantMap: Record<string, string[]>;
  nodes: Set<string>;
  parentMap: Record<string, string[]>;

  constructor(parentMap: {}, childMap: {}) {
    this.nodes = new Set([...Object.keys(parentMap), ...Object.keys(childMap)]);
    this.parentMap = parentMap;
    this.childMap = childMap;
    this.ancestorMap = {};
    this.descendantMap = {};
  }

  getAncestors(node: string) {
    if (!(node in this.ancestorMap)) {
      let ancestors: Set<string> = new Set();
      if (node in this.parentMap) {
        for (let parent of this.parentMap[node]) {
          ancestors.add(parent);
          for (let ancestor of this.getAncestors(parent)) {
            ancestors.add(ancestor);
          }
        }
      }

      this.ancestorMap[node] = [...ancestors];
    }

    return this.ancestorMap[node];
  }

  getDescendants(node: string) {
    if (!(node in this.descendantMap)) {
      let descendants: Set<string> = new Set();

      if (node in this.childMap) {
        for (let child of this.childMap[node]) {
          descendants.add(child);
          for (let descendant of this.getDescendants(child)) {
            descendants.add(descendant);
          }
        }
      }

      this.descendantMap[node] = [...descendants];
    }

    return this.descendantMap[node];
  }

  updateCodeToStatus(
    codeToStatus: { [key: string]: "+" | "(+)" | "-" | "(-)" | "!" | "?" },
    code: string,
    status: string,
  ): { [key: string]: "+" | "(+)" | "-" | "(-)" | "!" | "?" } {
    // Given mapping from codes to statuses, a code, and that code's new
    // status, return an updated mapping.

    let included = Object.keys(codeToStatus).filter(
      (c) => codeToStatus[c] === "+" && c !== code,
    );
    let excluded = Object.keys(codeToStatus).filter(
      (c) => codeToStatus[c] === "-" && c !== code,
    );

    if (status === "+" && codeToStatus[code] !== "+") {
      included.push(code);
    } else if (status === "-" && codeToStatus[code] !== "-") {
      excluded.push(code);
    }

    const updatedCodeToStatus: {
      [key: string]: "+" | "(+)" | "-" | "(-)" | "!" | "?";
    } = {};
    this.nodes.forEach((code1: string) => {
      if (code1 === code || this.getDescendants(code).includes(code1)) {
        updatedCodeToStatus[code1] = this.codeStatus(code1, included, excluded);
      } else {
        updatedCodeToStatus[code1] = codeToStatus[code1];
      }
    });
    return updatedCodeToStatus;
  }

  codeStatus(
    code: string,
    included: string | string[],
    excluded: string | string[],
  ) {
    // Return status of code, given lists of codes that are included and excluded.

    if (included.includes(code)) {
      // this code is explicitly included
      return "+";
    }

    if (excluded.includes(code)) {
      // this code is explicitly excluded
      return "-";
    }

    const { excludedAncestors, includedAncestors } = this.significantAncestors(
      code,
      included,
      excluded,
    );

    if (includedAncestors.length === 0 && excludedAncestors.length === 0) {
      // no ancestors are included or excluded, so this code is neither excluded or
      // excluded
      return "?";
    }

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

  significantAncestors(
    code: string,
    included: string | string[],
    excluded: string | string[],
  ) {
    // Find ancestors of code which are both:
    //   * members of included or excluded, and
    //   * not overridden by any of their descendants
    //
    // If A is an ancestor of B and B is an ancestor of C, then we say that B overrides
    // A because B is closer to C than A.

    const ancestors = this.getAncestors(code);

    // these are the ancestors of the code that are directly included or excluded
    const includedOrExcludedAncestors = ancestors.filter(
      (a: string) => included.includes(a) || excluded.includes(a),
    );

    // these are the ancestors of the code that are directly included or excluded,
    // and which are not overridden by any of their descendants
    const significantAncestors = includedOrExcludedAncestors.filter(
      (a: string) =>
        !this.getDescendants(a).some((d: string) =>
          includedOrExcludedAncestors.includes(d),
        ),
    );

    return {
      includedAncestors: significantAncestors.filter((a: string) =>
        included.includes(a),
      ),
      excludedAncestors: significantAncestors.filter((a: string) =>
        excluded.includes(a),
      ),
    };
  }

  treeRows(
    ancestorCode: string,
    codeToStatus: { [key: string]: "+" | "(+)" | "-" | "(-)" | "!" | "?" },
    codeToTerm: {
      [key: string]: string;
    },
    visiblePaths: Set<string>,
  ) {
    // Return array of objects representing rows in a "tree table" whose root
    // is at ancestorCode.  Rows are only included if they are reached by a
    // path which is in visiblePaths.  The returned objects are passed as props
    // to TreeRow components.

    const rows: {
      code: string;
      hasDescendants: boolean;
      isExpanded: boolean;
      path: string;
      pipes: ("└" | "├" | " " | "│")[];
      status: "+" | "(+)" | "-" | "(-)" | "!" | "?";
      term: string;
    }[] = [];

    const helper = (
      code: string,
      path: string,
      prevPipes: ("└" | "├" | " " | "│")[],
      isLastSibling: boolean,
    ) => {
      const childCodes = this.childMap[code] || [];
      childCodes.sort((code1: string | number, code2: string | number) => {
        const term1 = codeToTerm[code1];
        const term2 = codeToTerm[code2];
        if (term1 < term2) {
          return -1;
        } else if (term2 < term1) {
          return 1;
        } else {
          return 0;
        }
      });

      // A row is expanded if any of its children are visible.
      const isExpanded = childCodes.some((childCode: string) => {
        const childPath = path + ":" + childCode;
        return visiblePaths.has(childPath);
      });

      rows.push({
        code: code,
        status: codeToStatus[code],
        term: codeToTerm[code],
        path: path,
        pipes: prevPipes.concat(isLastSibling ? "└" : "├").slice(1),
        hasDescendants: childCodes.length > 0,
        isExpanded: isExpanded,
      });

      childCodes.forEach((childCode: string, ix: number) => {
        const childPath = path + ":" + childCode;
        if (visiblePaths.has(childPath)) {
          helper(
            childCode,
            childPath,
            prevPipes.concat(isLastSibling ? " " : "│"),
            ix === childCodes.length - 1,
          );
        }
      });
    };

    helper(ancestorCode, ancestorCode, [], true);

    return rows;
  }

  initiallyVisiblePaths(
    ancestorCodes: string[],
    codeToStatus: { [key: string]: "+" | "(+)" | "-" | "(-)" | "!" | "?" },
    maxDepth: number,
  ) {
    // Return set of paths which start at one of ancestorCodes, and end at
    // maxDepth codes below the first code where all descendants of that code
    // have the same status as that code.  These are the paths that should
    // initially be visible in a tree.
    //
    // Paths are strings of codes, separated by colons.
    //
    // So with this tree:
    //
    //        a
    //       / \
    //      b   c
    //     / \ / \
    //    d   e   f
    //   / \ / \ / \
    //  g   h   i   j
    //
    // and these statuses:
    //
    //        +
    //       / \
    //      -  (+)
    //     / \ / \
    //   (-) (-) (+)
    //   / \ / \ / \
    // (-) (-) (-) (+)
    //
    // the following paths would be initially visible if maxDepth = 0:
    //
    // {a, a:b, a:c, a:c:e, a:c:f, a:c:f:i, a:c:f:j}
    //
    // and following paths would be initially visible if maxDepth = 1:
    //
    // {a, a:b, a:b:d, a:b:e, a:c, a:c:e, a:c:e:h, a:c:e:i, a:c:f, a:c:f:i, a:c:f:j}

    const paths: Set<string> = new Set();

    const helper = (code: string, path: string, depth: number) => {
      // Walk the tree depth-first, collecting paths which should be visible.

      if (depth === maxDepth + 1) {
        // We have reached the maximum depth so need go no further.
        return;
      }

      paths.add(path);

      let newDepth: number;

      if (depth > 0) {
        // This code is a descendant of a code all of whose descendants have
        // the same status as it.
        newDepth = depth + 1;
      } else if (
        this.getDescendants(code).every((d) =>
          codeToStatus[d].includes(codeToStatus[code]),
        )
      ) {
        // All descendants of code have the same status as code.
        newDepth = 1;
      } else {
        newDepth = 0;
      }

      const childCodes = this.childMap[code] || [];
      childCodes.forEach((childCode: string) => {
        helper(childCode, path + ":" + childCode, newDepth);
      });
    };

    ancestorCodes.forEach((ancestorCode: string) => {
      helper(ancestorCode, ancestorCode, 0);
    });

    return paths;
  }

  toggleVisibility(
    visiblePaths: {
      has: (path: string) => boolean;
      delete: (path: string) => void;
      add: (path: string) => void;
    },
    path: string,
  ) {
    // Toggle the visibility of all children of the node at the given path.

    const code = path.split(":").slice(-1)[0];
    const childCodes = this.childMap[code] || [];
    childCodes.forEach((childCode: string) => {
      const childPath = path + ":" + childCode;
      if (visiblePaths.has(childPath)) {
        visiblePaths.delete(childPath);
      } else {
        visiblePaths.add(childPath);
      }
    });
  }
}

export default Hierarchy;
