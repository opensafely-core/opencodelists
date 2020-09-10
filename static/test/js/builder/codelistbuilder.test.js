"use strict";

import React from "react";
import { render, unmountComponentAtNode } from "react-dom";
import { act } from "react-dom/test-utils";

import CodelistBuilder from "../../../src/js/builder/codelistbuilder";
import Hierarchy from "../../../src/js/hierarchy";

// elbow.json was generated via generate_builder_fixture.
//
// It contains data for a codelist with a single search for "elbow", and the following
// concepts:
//
// Finding of elbow region (116309007)
// ├ Disorder of elbow (128133004)
// │ ├ Arthropathy of elbow (429554009)
// │ │ └ Arthritis of elbow (439656005)
// │ │   └ Lateral epicondylitis (202855006)
// │ ├ Enthesopathy of elbow region (35185008)
// │ │ └ Epicondylitis (73583000)
// │ │   └ Lateral epicondylitis (202855006)
// │ └ Soft tissue lesion of elbow region (239964003)
// └ Finding of elbow joint (298869002)
//   ├ Arthropathy of elbow (429554009)
//   │ └ Arthritis of elbow (439656005)
//   │   └ Lateral epicondylitis (202855006)
//   └ Elbow joint inflamed (298163003)
//     └ Arthritis of elbow (439656005)
//       └ Lateral epicondylitis (202855006)
//
// All concepts are in the ? state.

import * as data from "../fixtures/elbow.json";

let container = null;
beforeEach(() => {
  container = document.createElement("div");
  document.body.appendChild(container);
});

afterEach(() => {
  unmountComponentAtNode(container);
  container.remove();
  container = null;
});

it("renders total count correctly", () => {
  const hierarchy = new Hierarchy(data.parent_map, data.child_map);

  act(() => {
    render(
      <CodelistBuilder
        searches={data.searches}
        filter={data.filter}
        codeToStatus={data.code_to_status}
        tables={data.tables}
        isEditable={data.is_editable}
        updateURL={data.update_url}
        searchURL={data.search_url}
        hierarchy={hierarchy}
      />,
      container
    );

    expect(container.querySelector("#summary-total").textContent).toBe("10");
  });
});
