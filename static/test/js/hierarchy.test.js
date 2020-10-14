"use strict";

import Hierarchy from "../../src/js/hierarchy";

test("updateCodeToStatus", () => {
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

  expect(hierarchy.updateCodeToStatus(codeToStatus, "c", "-")).toEqual({
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
  });
});

test("codeStatus", () => {
  const hierarchy = buildTestHierarchy();

  function codeToStatus(included, excluded) {
    let codeToStatus = {};
    hierarchy.nodes.forEach((node) => {
      codeToStatus[node] = hierarchy.codeStatus(node, included, excluded);
    });
    return codeToStatus;
  }

  expect(codeToStatus([], [])).toEqual({
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

  expect(codeToStatus(["a"], [])).toEqual({
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

  expect(codeToStatus(["b"], ["c"])).toEqual({
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

  expect(codeToStatus(["a", "b"], [])).toEqual({
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

  expect(codeToStatus(["a"], ["b"])).toEqual({
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

  expect(codeToStatus(["a"], ["b", "c"])).toEqual({
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

  expect(codeToStatus(["a", "e"], ["b", "c"])).toEqual({
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
});

test("treeRows", () => {
  // a
  // ├ b
  // │ ├ d (not expanded)
  // │ └ e
  // │   ├ h
  // │   └ i
  // └ c
  //   ├ e (not expanded)
  //   └ f (not expanded)

  const hierarchy = buildTestHierarchy();
  const visiblePaths = new Set([
    "a",
    "a:b",
    "a:c",
    "a:b:d",
    "a:b:e",
    "a:c:e",
    "a:c:f",
    "a:b:e:h",
    "a:b:e:i",
  ]);

  // We're not testing whether the terms or statuses are returned correctly, so
  // we pass in empty objects here.
  const rows = hierarchy.treeRows("a", {}, {}, visiblePaths);

  expect(rows.map((row) => [row.path, row.isExpanded])).toEqual([
    ["a", true],
    ["a:b", true],
    ["a:b:d", false],
    ["a:b:e", true],
    ["a:b:e:h", false],
    ["a:b:e:i", false],
    ["a:c", true],
    ["a:c:e", false],
    ["a:c:f", false],
  ]);

  expect(rows.map((row) => row.pipes)).toEqual([
    [],
    ["├"],
    ["│", "├"],
    ["│", "└"],
    ["│", " ", "├"],
    ["│", " ", "└"],
    ["└"],
    [" ", "├"],
    [" ", "└"],
  ]);
});

test("initiallyVisiblePaths", () => {
  // With this hierarchy:
  //
  //        +
  //       / \
  //      -  (+)
  //     / \ / \
  //   (-) (-) (+)
  //   / \ / \ / \
  // (-) (-) (-) (+)
  //
  // Starting at a, the following paths are initially visible:
  //
  // a
  // ├ b (children not visible, because they are all (-))
  // └ c
  //   ├ e (children not visible, because they are all (-))
  //   └ f
  //     ├ i
  //     └ j

  const hierarchy = buildTestHierarchy();
  const codeToStatus = {
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
  };

  expect(hierarchy.initiallyVisiblePaths(["a"], codeToStatus)).toEqual(
    new Set(["a", "a:b", "a:c", "a:c:e", "a:c:f", "a:c:f:i", "a:c:f:j"])
  );
});

test("toggleVisibility", () => {
  // a
  // ├ b
  // │ ├ d (not expanded)
  // │ └ e
  // │   ├ h
  // │   └ i
  // └ c
  //   ├ e (not expanded)
  //   └ f (not expanded)

  const hierarchy = buildTestHierarchy();
  const visiblePaths = new Set([
    "a",
    "a:b",
    "a:c",
    "a:b:d",
    "a:b:e",
    "a:c:e",
    "a:c:f",
    "a:b:e:h",
    "a:b:e:i",
  ]);

  hierarchy.toggleVisibility(visiblePaths, "a:b:d");

  expect(visiblePaths).toEqual(
    new Set([
      "a",
      "a:b",
      "a:c",
      "a:b:d",
      "a:b:d:g", // Now visible
      "a:b:d:h", // Now visible
      "a:b:e",
      "a:c:e",
      "a:c:f",
      "a:b:e:h",
      "a:b:e:i",
    ])
  );

  hierarchy.toggleVisibility(visiblePaths, "a:b:d");

  expect(visiblePaths).toEqual(
    new Set([
      "a",
      "a:b",
      "a:c",
      "a:b:d",
      // "a:b:d:g",  Now not visible
      // "a:b:d:h",  Now not visible
      "a:b:e",
      "a:c:e",
      "a:c:f",
      "a:b:e:h",
      "a:b:e:i",
    ])
  );
});

function buildTestHierarchy() {
  // Return hierarchy with following structure:
  //
  //        a
  //       / \
  //      b   c
  //     / \ / \
  //    d   e   f
  //   / \ / \ / \
  //  g   h   i   j

  const parentMap = {
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
  };

  return new Hierarchy(parentMap, childMap);
}
