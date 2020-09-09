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

function buildTestHierarchy() {
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
