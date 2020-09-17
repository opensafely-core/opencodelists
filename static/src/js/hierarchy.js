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

export { Hierarchy as default };
