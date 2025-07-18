import "@testing-library/jest-dom";
import { act, render, screen, within } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import React from "react";
import { afterEach, beforeEach, expect, it, vi } from "vitest";
import Hierarchy from "../../../_hierarchy";
import MoreInfoModal from "../../../components/Codelist/MoreInfoModal";
import { Status } from "../../../types";
import * as versionWithCompleteSearchesData from "../../fixtures/version_with_complete_searches.json";

// Mock dependencies
vi.mock("../../../_utils", () => ({
  getCookie: vi.fn(() => "test-csrf-token"),
  readValueFromPage: () => ({ coding_system_id: "snomedct" }),
}));

beforeEach(() => {
  vi.stubGlobal(
    "fetch",
    vi.fn(() =>
      Promise.resolve({
        json: () =>
          Promise.resolve({
            synonyms: { "123": ["Alpha", "Beta", "Test Term"] },
            references: { "123": [["TestReference", "https://example.com"]] },
          }),
      }),
    ),
  );
});

afterEach(() => {
  vi.unstubAllGlobals();
});

const props = {
  allCodes: ["123", "456"],
  code: "123",
  codeToStatus: { "123": "+" as Status, "456": "-" as Status },
  codeToTerm: { "123": "Test Term", "456": "Other Term" },
  hierarchy: new Hierarchy(
    versionWithCompleteSearchesData.parent_map,
    versionWithCompleteSearchesData.child_map,
  ),
  status: "+" as Status,
  term: "Test Term",
};

it("renders More info button", () => {
  render(<MoreInfoModal {...props} />);
  expect(screen.getByRole("button", { name: /more info/i })).toBeVisible();
});

it("shows modal and fetches synonyms and references on button click", async () => {
  const user = userEvent.setup();
  render(<MoreInfoModal {...props} />);
  await user.click(screen.getByRole("button", { name: /more info/i }));

  const synonymsHeading = screen.getByRole("heading", { name: /synonyms/i });
  const synonymsList = synonymsHeading.nextElementSibling as HTMLUListElement;
  expect(within(synonymsList).getByText("Alpha")).toBeVisible();
  expect(within(synonymsList).getByText("Beta")).toBeVisible();

  // Although "Test Term" is returned as a synonym, it shouldn't display as
  // it matches the main term
  expect(within(synonymsList).queryByText("Test Term")).not.toBeInTheDocument();

  const referencesHeading = screen.getByRole("heading", {
    name: /references/i,
  });
  const referencesList =
    referencesHeading.nextElementSibling as HTMLUListElement;
  expect(within(referencesList).getByText("TestReference")).toBeVisible();
  expect(within(referencesList).getByText("TestReference")).toHaveAttribute(
    "href",
    "https://example.com",
  );

  expect(screen.getByText("Included")).toBeVisible();
});

it("shows 'No synonyms' if synonyms is empty", async () => {
  const user = userEvent.setup();
  render(<MoreInfoModal {...props} code="456" />);
  user.click(screen.getByRole("button", { name: /more info/i }));
  expect(await screen.findByText(/no synonyms/i)).toBeVisible();
});

it("shows 'No synonyms' if fetch fails", async () => {
  vi.stubGlobal(
    "fetch",
    vi.fn(() => Promise.reject("fail")),
  );
  const user = userEvent.setup();
  render(<MoreInfoModal {...props} />);

  await act(async () => {
    await user.click(screen.getByRole("button", { name: /more info/i }));
  });
  expect(await screen.findByText(/no synonyms/i)).toBeVisible();
});

it("shows 'No synonyms' if fetch succeeds but has an error message", async () => {
  vi.stubGlobal(
    "fetch",
    vi.fn(() =>
      Promise.resolve({
        json: () =>
          Promise.resolve({
            error: "an error occurred",
          }),
      }),
    ),
  );
  const user = userEvent.setup();
  render(<MoreInfoModal {...props} />);

  await user.click(screen.getByRole("button", { name: /more info/i }));
  expect(await screen.findByText(/no synonyms/i)).toBeVisible();
});

it("show 'No synonyms' if the only synonym matches the primary term", async () => {
  vi.stubGlobal(
    "fetch",
    vi.fn(() =>
      Promise.resolve({
        json: () =>
          Promise.resolve({
            synonyms: { "123": ["Test Term"] },
          }),
      }),
    ),
  );
  const user = userEvent.setup();
  render(<MoreInfoModal {...props} />);
  await user.click(screen.getByRole("button", { name: /more info/i }));
  expect(await screen.findByText(/no synonyms/i)).toBeVisible();
});
