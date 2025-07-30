import "@testing-library/jest-dom";
import { render } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import React from "react";
import { beforeEach, describe, expect, it, vi } from "vitest";
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
          parseInt(document.querySelector(`#summary-${key}`).textContent),
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

describe("Metadata Editing", () => {
  beforeEach(() => {
    vi.clearAllMocks();
    // Mock fetch to return updated metadata
    global.fetch = vi.fn().mockImplementation((_url, config) =>
      Promise.resolve({
        json: () =>
          Promise.resolve({
            metadata: {
              description: {
                text:
                  JSON.parse(config.body).description || "Initial description",
                html: `<p>${JSON.parse(config.body).description || "Initial description"}</p>`,
              },
              methodology: {
                text:
                  JSON.parse(config.body).methodology || "Initial methodology",
                html: `<p>${JSON.parse(config.body).methodology || "Initial methodology"}</p>`,
              },
              references: JSON.parse(config.body).references || [],
            },
          }),
      }),
    );
  });

  const setupMetadataTest = () => {
    const data = {
      ...versionWithNoSearchesData,
      metadata: {
        ...versionWithNoSearchesData.metadata,
        description: {
          text: "Initial description",
          html: "<p>Initial description</p>",
          isEditing: false,
        },
        methodology: {
          text: "Initial methodology",
          html: "<p>Initial methodology</p>",
          isEditing: false,
        },
        references: [{ text: "Initial reference", url: "http://example.com" }],
      },
    };

    return { data };
  };

  it("handles methodology field", async () => {
    const { data, visiblePaths, hierarchy } = setupMetadataTest();

    renderCodelistBuilder(data, hierarchy, visiblePaths);

    // Switch to metadata tab
    const metadataTab = document.querySelector(
      '[role="tab"][data-rb-event-key="metadata"]',
    );
    await userEvent.click(metadataTab);

    // Click edit button
    const editButton = document.querySelector(
      'button[title="Edit methodology"]',
    );
    await userEvent.click(editButton);

    // Find textarea
    const textarea = document.querySelector("textarea#methodology");
    expect(textarea).toBeInTheDocument();
    expect(textarea).toHaveValue("Initial methodology");

    // Type new content
    await userEvent.clear(textarea);
    await userEvent.type(textarea, "Updated methodology");

    // Cancel
    const cancelButton = document.querySelector(
      'button[title="Cancel methodology edit"]',
    );
    await userEvent.click(cancelButton);

    // Wait to ensure no API call was made
    await vi.waitFor(() => {
      expect(fetch).not.toHaveBeenCalled();
    });

    // Verify content remains unchanged
    const methodologyText = document.querySelector(
      ".methodology .builder__markdown",
    );
    expect(methodologyText).toHaveTextContent("Initial methodology");

    // Verify edit mode is exited
    expect(textarea).not.toBeInTheDocument();
  });

  it("handles reference management", async () => {
    // helper for finding and clicking a button based on its text
    const clickButton = async (buttonText) => {
      const button = document.evaluate(
        `//button[text()='${buttonText}']`,
        document,
        null,
        XPathResult.FIRST_ORDERED_NODE_TYPE,
        null,
      ).singleNodeValue;
      await userEvent.click(button);
    };

    // helper for finding and entering text in an input field based on its placeholder
    const enterText = async (placeholder, text) => {
      const input = document.querySelector(
        `input[placeholder="${placeholder}"]`,
      );
      if (!input) {
        throw new Error(`Input with placeholder '${placeholder}' not found`);
      }
      await userEvent.clear(input);
      await userEvent.type(input, text);
    };

    const { data, visiblePaths, hierarchy } = setupMetadataTest();

    renderCodelistBuilder(data, hierarchy, visiblePaths);

    // Switch to metadata tab
    const metadataTab = document.querySelector(
      '[role="tab"][data-rb-event-key="metadata"]',
    );
    await userEvent.click(metadataTab);

    // Verify initial reference is displayed
    const referenceLink = document.querySelector(
      'a[href="http://example.com"]',
    );
    expect(referenceLink).toBeInTheDocument();
    expect(referenceLink).toHaveTextContent("Initial reference");

    await clickButton("Add another reference");

    // Fill in new reference form
    await enterText("Text to display", "New reference");
    await enterText("URL to link to", "http://example.org");

    // First let's test cancel
    await clickButton("Cancel");

    // inputs should not be visible
    await expect(
      enterText("Text to display", "New reference"),
    ).rejects.toThrowError(
      "Input with placeholder 'Text to display' not found",
    );
    await expect(
      enterText("URL to link to", "http://example.org"),
    ).rejects.toThrowError("Input with placeholder 'URL to link to' not found");

    await clickButton("Add another reference");

    // Fill in new reference form
    await enterText("Text to display", "New reference");
    await enterText("URL to link to", "http://example.org");

    // Save reference
    await clickButton("Save");

    // Wait for API call and state update
    await vi.waitFor(() => {
      expect(fetch).toHaveBeenCalledWith(
        data.update_url,
        expect.objectContaining({
          method: "POST",
          body: expect.stringContaining(
            '"references":[{"text":"Initial reference","url":"http://example.com"},{"text":"New reference","url":"http://example.org"}]',
          ),
        }),
      );
    });

    // Verify reference is added to the UI
    const newReferenceLink = document.querySelector(
      'a[href="http://example.org"]',
    );
    expect(newReferenceLink).toBeInTheDocument();
    expect(newReferenceLink).toHaveTextContent("New reference");

    // Verify form is reset and that inputs are not be visible
    await expect(
      enterText("Text to display", "New reference"),
    ).rejects.toThrowError(
      "Input with placeholder 'Text to display' not found",
    );
    await expect(
      enterText("URL to link to", "http://example.org"),
    ).rejects.toThrowError("Input with placeholder 'URL to link to' not found");
  });
});
