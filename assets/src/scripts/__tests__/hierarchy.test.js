import { expect, test } from "vitest";
import Hierarchy from "../hierarchy";

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
    a: "?",
    b: "+",
    c: "?",
    d: "(+)",
    e: "(+)",
    f: "?",
    g: "(+)",
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
  const hierarchy = buildTestHierarchy();
  const codeToStatus = {
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
  };

  // Starting at a, the following paths are initially visible with maxDepth = 0:
  //
  // a
  // ├ b (children not visible, because they are all (-))
  // └ c
  //   ├ e (children not visible, because they are all (-))
  //   └ f
  //     ├ i
  //     └ j

  expect(hierarchy.initiallyVisiblePaths(["a"], codeToStatus, 0)).toEqual(
    new Set(["a", "a:b", "a:c", "a:c:e", "a:c:f", "a:c:f:i", "a:c:f:j"]),
  );

  // Starting at a, the following paths are initially visible with maxDepth = 1:
  //
  // a
  // ├ b (immediate children visible, because maxDepth = 1)
  // │ ├ d
  // │ └ e
  // └ c
  //   ├ e (immediate children visible, because maxDepth = 1)
  //   │ ├ h
  //   │ └ i
  //   └ f
  //     ├ i
  //     └ j

  expect(hierarchy.initiallyVisiblePaths(["a"], codeToStatus, 1)).toEqual(
    new Set([
      "a",
      "a:b",
      "a:b:d",
      "a:b:e",
      "a:c",
      "a:c:e",
      "a:c:e:h",
      "a:c:e:i",
      "a:c:f",
      "a:c:f:i",
      "a:c:f:j",
    ]),
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
    ]),
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
    ]),
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
