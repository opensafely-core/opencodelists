"use strict";

import React from "react";
import { render, unmountComponentAtNode } from "react-dom";
import { act } from "react-dom/test-utils";
import "@testing-library/jest-dom";

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

// Not sure if this is the best approach, but it works!
global.fetch = jest.fn().mockImplementation((url, config) =>
  Promise.resolve({
    json: () => Promise.resolve(JSON.parse(config.body)),
  })
);

it("does the right thing when clicking around", () => {
  const hierarchy = new Hierarchy(data.parent_map, data.child_map);
  const ancestorCodes = data.tree_tables
    .map(([_, ancestorCodes]) => ancestorCodes) // eslint-disable-line no-unused-vars
    .flat();
  const visiblePaths = hierarchy.initiallyVisiblePaths(
    ancestorCodes,
    data.code_to_status,
    100 // we want all codes to be visible so that we can check statuses
  );

  // Keep track of which concept has which status
  const statuses = {
    116309007: "?", // Finding of elbow region
    128133004: "?", // Disorder of elbow
    239964003: "?", // Soft tissue lesion of elbow region
    35185008: "?", // Enthesopathy of elbow region
    73583000: "?", // Epicondylitis
    202855006: "?", // Lateral epicondylitis
    429554009: "?", // Arthropathy of elbow
    439656005: "?", // Arthritis of elbow
    298869002: "?", // Finding of elbow joint
    298163003: "?", // Elbow joint inflamed
  };

  // Keep track of how many concepts we expect to have each status
  const summaryCounts = {
    total: 10,
    included: 0,
    excluded: 0,
    unresolved: 10,
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
        includedCodes={data.included_codes}
        excludedCodes={data.excluded_codes}
        displayedCodes={data.displayed_codes}
        isEditable={data.is_editable}
        updateURL={data.update_url}
        searchURL={data.search_url}
        downloadURL={data.download_url}
        hierarchy={hierarchy}
      />,
      container
    );
  });

  checkSummary();
  checkStatus();

  act(() => {
    click("298163003", "+");
  });

  summaryCounts.included += 3;
  summaryCounts.unresolved -= 3;

  statuses["298163003"] = "+";
  statuses["439656005"] = "(+)";
  statuses["202855006"] = "(+)";

  checkSummary();
  checkStatus();

  act(() => {
    click("429554009", "-");
  });

  summaryCounts.included -= 2;
  summaryCounts.excluded += 1;
  summaryCounts.unresolved -= 1;
  summaryCounts["in-conflict"] += 2;

  statuses["429554009"] = "-";
  statuses["439656005"] = "!";
  statuses["202855006"] = "!";

  checkSummary();
  checkStatus();
});
