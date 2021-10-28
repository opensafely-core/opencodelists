class Hierarchy {
  constructor(parentMap, childMap) {
    this.nodes = new Set([...Object.keys(parentMap), ...Object.keys(childMap)]);
    this.parentMap = parentMap;
    this.childMap = childMap;
    this.ancestorMap = {};
    this.descendantMap = {};
  }

  getAncestors(node) {
    if (!(node in this.ancestorMap)) {
      let ancestors = new Set();
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

  getDescendants(node) {
    if (!(node in this.descendantMap)) {
      let descendants = new Set();
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

  updateCodeToStatus(codeToStatus, code, symbol) {
    // Given mapping from codes to statuses, a code, and the symbol that's been clicked
    // on, return an updated mapping.

    let included = Object.keys(codeToStatus).filter(
      (c) => codeToStatus[c] === "+" && c !== code
    );
    let excluded = Object.keys(codeToStatus).filter(
      (c) => codeToStatus[c] === "-" && c !== code
    );

    if (symbol === "+" && codeToStatus[code] !== "+") {
      included.push(code);
    } else if (symbol === "-" && codeToStatus[code] !== "-") {
      excluded.push(code);
    }

    const updatedCodeToStatus = {};
    this.nodes.forEach((code1) => {
      if (code1 === code || this.getDescendants(code).includes(code1)) {
        updatedCodeToStatus[code1] = this.codeStatus(code1, included, excluded);
      } else {
        updatedCodeToStatus[code1] = codeToStatus[code1];
      }
    });
    return updatedCodeToStatus;
  }

  codeStatus(code, included, excluded) {
    // Return status of code, given lists of codes that are included and excluded.

    if (included.includes(code)) {
      // this code is explicitly included
      return "+";
    }

    if (excluded.includes(code)) {
      // this code is explicitly excluded
      return "-";
    }

    const { includedAncestors, excludedAncestors } = this.significantAncestors(
      code,
      included,
      excluded
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

  significantAncestors(code, included, excluded) {
    // Find ancestors of code which are both:
    //   * members of included or excluded, and
    //   * not overridden by any of their descendants
    //
    // If A is an ancestor of B and B is an ancestor of C, then we say that B overrides
    // A because B is closer to C than A.

    const ancestors = this.getAncestors(code);

    // these are the ancestors of the code that are directly included or excluded
    const includedOrExcludedAncestors = ancestors.filter(
      (a) => included.includes(a) || excluded.includes(a)
    );

    // these are the ancestors of the code that are directly included or excluded,
    // and which are not overridden by any of their descendants
    const significantAncestors = includedOrExcludedAncestors.filter(
      (a) =>
        !this.getDescendants(a).some((d) =>
          includedOrExcludedAncestors.includes(d)
        )
    );

    return {
      includedAncestors: significantAncestors.filter((a) =>
        included.includes(a)
      ),
      excludedAncestors: significantAncestors.filter((a) =>
        excluded.includes(a)
      ),
    };
  }

  allDescendantsHaveSameStatus(code, codeToStatus) {
    return this.getDescendants(code).every((descendantCode) =>
      codeToStatus[descendantCode].includes(codeToStatus[code])
    );
  }
}

export { Hierarchy as default };
