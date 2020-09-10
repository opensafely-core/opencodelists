"use strict";

import React from "react";
import { render, unmountComponentAtNode } from "react-dom";
import { act } from "react-dom/test-utils";

import CodelistBuilder from "../../../src/js/builder/codelistbuilder";
import Hierarchy from "../../../src/js/hierarchy";

// elbow.json was generated via generate_builder_fixture
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

    expect(container.querySelector("#summary-total").textContent).toBe("49");
  });
});
