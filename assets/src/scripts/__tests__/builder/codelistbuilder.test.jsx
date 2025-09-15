import "@testing-library/jest-dom";
import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { expect, it, vi } from "vitest";
import Hierarchy from "../../_hierarchy";
import CodelistBuilder from "../../components/CodelistBuilder";
// See builder/management/commands/generate_builder_fixtures.py and
// opencodelists/tests/fixtures.py for details about what these fixtures contain.
import * as versionFromScratchData from "../fixtures/version_from_scratch.json";
import * as versionWithCompleteSearchesData from "../fixtures/version_with_complete_searches.json";
import * as versionWithNoSearchesData from "../fixtures/version_with_no_searches.json";
import * as versionWithSomeSearchesData from "../fixtures/version_with_some_searches.json";

// Not sure if this is the best approach, but it works!
global.fetch = vi.fn().mockImplementation((_url, config) =>
  Promise.resolve({
    json: () => Promise.resolve(JSON.parse(config.body)),
  }),
);

const renderCodelistBuilder = (data, hierarchy, visiblePaths) => {
  if (!hierarchy) {
    hierarchy = new Hierarchy(data.parent_map, data.child_map);
  }
  if (!visiblePaths) {
    const ancestorCodes = data.tree_tables.flatMap(
      ([_, ancestorCodes]) => ancestorCodes,
    );
    visiblePaths = hierarchy.initiallyVisiblePaths(
      ancestorCodes,
      data.code_to_status,
      1,
    );
  }

  render(
    <CodelistBuilder
      allCodes={data.all_codes}
      codeToStatus={data.code_to_status}
      codeToTerm={data.code_to_term}
      draftURL={data.draft_url}
      hierarchy={hierarchy}
      isEditable={data.is_editable}
      isEmptyCodelist={data.is_empty_codelist}
      metadata={data.metadata}
      resultsHeading={data.results_heading}
      searches={data.searches}
      searchURL={data.search_url}
      treeTables={data.tree_tables}
      updateURL={data.update_url}
      versions={data.versions}
      visiblePaths={visiblePaths}
    />,
  );
};

it("renders version_with_no_searches without error", () => {
  renderCodelistBuilder(versionWithNoSearchesData);
});

it("renders version_with_some_searches without error", () => {
  renderCodelistBuilder(versionWithSomeSearchesData);
});

it("renders version_with_complete_searches without error", () => {
  renderCodelistBuilder(versionWithCompleteSearchesData);
});

it("renders version_from_scratch without error", () => {
  renderCodelistBuilder(versionFromScratchData);
});

it("does the right thing when clicking around", async () => {
  const data = versionWithSomeSearchesData;
  const hierarchy = new Hierarchy(data.parent_map, data.child_map);
  const ancestorCodes = data.tree_tables.flatMap(
    ([_, ancestorCodes]) => ancestorCodes,
  );
  const visiblePaths = hierarchy.initiallyVisiblePaths(
    ancestorCodes,
    data.code_to_status,
    100, // we want all codes to be visible so that we can check statuses
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
      const row = document.querySelector(`[data-code='${code}']`);

      switch (statuses[code]) {
        case "+":
          expect(row.querySelector("button[data-symbol='+']")).toHaveClass(
            "btn-primary",
          );
          break;
        case "(+)":
          expect(row.querySelector("button[data-symbol='+']")).toHaveClass(
            "btn-secondary",
          );
          break;
        case "-":
          expect(row.querySelector("button[data-symbol='-']")).toHaveClass(
            "btn-primary",
          );
          break;
        case "(-)":
          expect(row.querySelector("button[data-symbol='-']")).toHaveClass(
            "btn-secondary",
          );
          break;
        case "?":
          expect(row.querySelector("button[data-symbol='+']")).not.toHaveClass(
            "btn-primary",
          );
          expect(row.querySelector("button[data-symbol='+']")).not.toHaveClass(
            "btn-secondary",
          );
          expect(row.querySelector("button[data-symbol='-']")).not.toHaveClass(
            "btn-primary",
          );
          expect(row.querySelector("button[data-symbol='-']")).not.toHaveClass(
            "btn-secondary",
          );
          break;
        case "!":
          break;
      }
    });
  };

  const checkSummary = () => {
    Object.keys(summaryCounts).forEach((key) => {
      if (key === "total") return; // We don't display the total
      if (summaryCounts[key] === 0) {
        expect(document.querySelector(`#summary-${key}`)).toBe(null);
      } else {
        expect(
          parseInt(document.querySelector(`#summary-${key}`).textContent, 10),
        ).toBe(summaryCounts[key]);
      }
    });
  };

  // Helper that simulates clicking on + or - for given code.
  const findClick = (code, symbol) => {
    return document.querySelector(
      `[data-code='${code}'] button[data-symbol='${symbol}']`,
    );
  };

  renderCodelistBuilder(data, hierarchy, visiblePaths);

  checkSummary();
  checkStatus();

  await userEvent.click(findClick("35185008", "-")); // Exclude Enthesopathy of elbow region

  summaryCounts.excluded += 2;
  summaryCounts["in-conflict"] += 1;
  summaryCounts.included -= 3;

  statuses["35185008"] = "-"; // Enthesopathy of elbow region
  statuses["73583000"] = "(-)"; // Epicondylitis
  statuses["202855006"] = "!"; // Lateral epicondylitis

  checkSummary();
  checkStatus();

  await userEvent.click(findClick("35185008", "-")); // Un-exclude Enthesopathy of elbow region

  summaryCounts.excluded -= 2;
  summaryCounts["in-conflict"] -= 1;
  summaryCounts.included += 3;

  statuses["35185008"] = "(+)"; // Enthesopathy of elbow region
  statuses["73583000"] = "(+)"; // Epicondylitis
  statuses["202855006"] = "(+)"; // Lateral epicondylitis

  checkSummary();
  checkStatus();
});

it("switches tabs when the tab is clicked", async () => {
  const user = userEvent.setup();
  renderCodelistBuilder(versionWithNoSearchesData);

  // Initially, the codelist tab should be active
  expect(
    screen.getByRole("tab", { name: "Codelist", selected: true }),
  ).toBeVisible();
  expect(
    screen.getByRole("tab", { name: "Metadata", selected: false }),
  ).toBeVisible();

  await user.click(screen.getByRole("tab", { name: "Metadata" }));

  // The metadata tab should now be active
  expect(
    screen.getByRole("tab", { name: "Codelist", selected: false }),
  ).toBeVisible();
  expect(
    screen.getByRole("tab", { name: "Metadata", selected: true }),
  ).toBeVisible();

  expect(document.querySelector(".builder__metadata-forms")).toBeVisible();
});

it("renders the metadata tab when the URL has #metadata", () => {
  window.location.hash = "#metadata"; // Simulate the URL having #metadata
  renderCodelistBuilder(versionWithNoSearchesData);

  // The metadata tab should be active
  expect(
    screen.getByRole("tab", { name: "Codelist", selected: false }),
  ).toBeVisible();
  expect(
    screen.getByRole("tab", { name: "Metadata", selected: true }),
  ).toBeVisible();

  expect(document.querySelector(".builder__metadata-forms")).toBeVisible();
});
