"use strict";

import React from "react";
import { render, unmountComponentAtNode } from "react-dom";
import { act } from "react-dom/test-utils";
import "@testing-library/jest-dom";

import CodelistBuilder from "../../../src/js/builder/codelistbuilder";
import Hierarchy from "../../../src/js/hierarchy";

// See builder/management/commands/generate_builder_fixtures.py and
// opencodelists/tests/fixtures.py for details about what these fixtures contain.
import * as versionWithNoSearchesData from "../fixtures/version_with_no_searches.json";
import * as versionWithSomeSearchesData from "../fixtures/version_with_some_searches.json";
import * as versionWithCompleteSearchesData from "../fixtures/version_with_complete_searches.json";
import * as versionFromScratchData from "../fixtures/version_from_scratch.json";

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

// Not sure if this is the best approach, but it works!
global.fetch = jest.fn().mockImplementation((url, config) =>
  Promise.resolve({
    json: () => Promise.resolve(JSON.parse(config.body)),
  })
);

const testRender = (data) => {
  const hierarchy = new Hierarchy(data.parent_map, data.child_map);
  const ancestorCodes = data.tree_tables
    .map(([_, ancestorCodes]) => ancestorCodes) // eslint-disable-line no-unused-vars
    .flat();
  const visiblePaths = hierarchy.initiallyVisiblePaths(
    ancestorCodes,
    data.code_to_status,
    1
  );

  act(() => {
    render(
      <CodelistBuilder
        searches={data.searches}
        filter={data.filter}
        treeTables={data.tree_tables}
        codeToStatus={data.code_to_status}
        codeToTerm={data.code_to_term}
        visiblePaths={visiblePaths}
        allCodes={data.all_codes}
        includedCodes={data.included_codes}
        excludedCodes={data.excluded_codes}
        isEditable={data.is_editable}
        updateURL={data.update_url}
        searchURL={data.search_url}
        versions={data.versions}
        metadata={data.metadata}
        hierarchy={hierarchy}
      />,
      container
    );
  });
};

it("renders version_with_no_searches without error", () => {
  testRender(versionWithNoSearchesData);
});

it("renders version_with_some_searches without error", () => {
  testRender(versionWithSomeSearchesData);
});

it("renders version_with_complete_searches without error", () => {
  testRender(versionWithCompleteSearchesData);
});

it("renders version_from_scratch without error", () => {
  testRender(versionFromScratchData);
});

it("does the right thing when clicking around", () => {
  const data = versionWithSomeSearchesData;
  const hierarchy = new Hierarchy(data.parent_map, data.child_map);
  const ancestorCodes = data.tree_tables
    .map(([_, ancestorCodes]) => ancestorCodes) // eslint-disable-line no-unused-vars
    .flat();
  const visiblePaths = hierarchy.initiallyVisiblePaths(
    ancestorCodes,
    data.code_to_status,
    100 // we want all codes to be visible so that we can check statuses
  );

  // Keep track of which visible concept has which status
  const statuses = {
    128133004: "+", // Disorder of elbow
    239964003: "(+)", // Soft tissue lesion of elbow region
    35185008: "(+)", // Enthesopathy of elbow region
    73583000: "(+)", // Epicondylitis
    202855006: "(+)", // Lateral epicondylitis
    429554009: "(+)", // Arthropathy of elbow
    439656005: "+", // Arthritis of elbow
    3723001: "-", // Arthritis
    156659008: "+", // (Epicondylitis &/or tennis elbow) or (golfers' elbow)
  };

  // Keep track of how many concepts we expect to have each status
  const summaryCounts = {
    total: 9,
    included: 8,
    excluded: 1,
    unresolved: 0,
    "in-conflict": 0,
  };

  const checkStatus = () => {
    Object.keys(statuses).forEach((code) => {
      const row = container.querySelector(`[data-code='${code}']`);

      switch (statuses[code]) {
        case "+":
          expect(row.querySelector("button[data-symbol='+']")).toHaveClass(
            "btn-primary"
          );
          break;
        case "(+)":
          expect(row.querySelector("button[data-symbol='+']")).toHaveClass(
            "btn-secondary"
          );
          break;
        case "-":
          expect(row.querySelector("button[data-symbol='-']")).toHaveClass(
            "btn-primary"
          );
          break;
        case "(-)":
          expect(row.querySelector("button[data-symbol='-']")).toHaveClass(
            "btn-secondary"
          );
          break;
        case "?":
          expect(row.querySelector("button[data-symbol='+']")).not.toHaveClass(
            "btn-primary"
          );
          expect(row.querySelector("button[data-symbol='+']")).not.toHaveClass(
            "btn-secondary"
          );
          expect(row.querySelector("button[data-symbol='-']")).not.toHaveClass(
            "btn-primary"
          );
          expect(row.querySelector("button[data-symbol='-']")).not.toHaveClass(
            "btn-secondary"
          );
          break;
        case "!":
          break;
      }
    });
  };

  const checkSummary = () => {
    Object.keys(summaryCounts).forEach((key) => {
      if (summaryCounts[key] === 0) {
        expect(container.querySelector(`#summary-${key}`)).toBe(null);
      } else {
        expect(
          parseInt(container.querySelector(`#summary-${key}`).textContent)
        ).toBe(summaryCounts[key]);
      }
    });
  };

  // Helper that simulates clicking on + or - for given code.
  const click = (code, symbol) => {
    const button = container.querySelector(
      `[data-code='${code}'] button[data-symbol='${symbol}']`
    );
    button.dispatchEvent(new MouseEvent("click", { bubbles: true }));
  };

  act(() => {
    render(
      <CodelistBuilder
        searches={data.searches}
        filter={data.filter}
        treeTables={data.tree_tables}
        codeToStatus={data.code_to_status}
        codeToTerm={data.code_to_term}
        visiblePaths={visiblePaths}
        allCodes={data.all_codes}
        includedCodes={data.included_codes}
        excludedCodes={data.excluded_codes}
        isEditable={data.is_editable}
        updateURL={data.update_url}
        searchURL={data.search_url}
        versions={data.versions}
        metadata={data.metadata}
        hierarchy={hierarchy}
      />,
      container
    );
  });

  checkSummary();
  checkStatus();

  act(() => {
    click("35185008", "-"); // Exclude Enthesopathy of elbow region
  });

  summaryCounts.excluded += 2;
  summaryCounts["in-conflict"] += 1;
  summaryCounts.included -= 3;

  statuses["35185008"] = "-"; // Enthesopathy of elbow region
  statuses["73583000"] = "(-)"; // Epicondylitis
  statuses["202855006"] = "!"; // Lateral epicondylitis

  checkSummary();
  checkStatus();

  act(() => {
    click("35185008", "-"); // Un-exclude Enthesopathy of elbow region
  });

  summaryCounts.excluded -= 2;
  summaryCounts["in-conflict"] -= 1;
  summaryCounts.included += 3;

  statuses["35185008"] = "(+)"; // Enthesopathy of elbow region
  statuses["73583000"] = "(+)"; // Epicondylitis
  statuses["202855006"] = "(+)"; // Lateral epicondylitis

  checkSummary();
  checkStatus();
});
