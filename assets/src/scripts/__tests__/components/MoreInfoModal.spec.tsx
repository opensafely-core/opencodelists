import "@testing-library/jest-dom";
import {
  fireEvent,
  render,
  screen,
  waitFor,
  within,
} from "@testing-library/react";
import React from "react";
import { afterEach, beforeEach, expect, it, vi } from "vitest";
import Hierarchy from "../../_hierarchy";
import MoreInfoModal from "../../components/MoreInfoModal";
import { Status } from "../../types";
import * as versionWithCompleteSearchesData from "../fixtures/version_with_complete_searches.json";

// Mock dependencies
vi.mock("../../_utils", () => ({
  getCookie: vi.fn(() => "test-csrf-token"),
  readValueFromPage: () => ({ coding_system_id: "snomedct" }),
}));

// @ts-ignore
const renderMoreInfoModal = (data, code = "123") => {
  const hierarchy = new Hierarchy(data.parent_map, data.child_map);
  const defaultProps = {
    allCodes: ["123", "456"],
    code,
    codeToStatus: { "123": "+" as Status, "456": "-" as Status },
    codeToTerm: { "123": "Test Term", "456": "Other Term" },
    hierarchy,
    status: "+" as Status,
    term: "Test Term",
  };
  render(<MoreInfoModal {...defaultProps} />);
};

beforeEach(() => {
  // @ts-ignore
  global.fetch = vi.fn(() =>
    Promise.resolve({
      json: () =>
        Promise.resolve({
          synonyms: { "123": ["Alpha", "Beta", "Test Term"] },
        }),
    }),
  );
});

afterEach(() => {
  vi.resetAllMocks();
});

it("renders More info button", () => {
  renderMoreInfoModal(versionWithCompleteSearchesData);
  expect(
    screen.getByRole("button", { name: /more info/i }),
  ).toBeInTheDocument();
});

it("shows modal and fetches synonyms on button click", async () => {
  renderMoreInfoModal(versionWithCompleteSearchesData);
  fireEvent.click(screen.getByRole("button", { name: /more info/i }));

  await waitFor(() => {
    const synonymsHeading = screen.getByRole("heading", { name: /synonyms/i });
    const synonymsList = synonymsHeading.nextElementSibling as HTMLUListElement;
    expect(within(synonymsList).getByText("Alpha")).toBeInTheDocument();
    expect(within(synonymsList).getByText("Beta")).toBeInTheDocument();

    // Although "Test Term" is returned as a synonym, it shouldn't display as
    // it matches the main term
    expect(
      within(synonymsList).queryByText("Test Term"),
    ).not.toBeInTheDocument();
  });

  expect(screen.getByText("Included")).toBeInTheDocument();
});

it("shows 'No synonyms' if synonyms is empty", async () => {
  renderMoreInfoModal(versionWithCompleteSearchesData, "456");
  fireEvent.click(screen.getByRole("button", { name: /more info/i }));

  await waitFor(() => {
    expect(screen.getByText(/no synonyms/i)).toBeInTheDocument();
  });
});

it("shows 'No synonyms' if fetch fails", async () => {
  // @ts-ignore
  global.fetch = vi.fn(() => Promise.reject("fail"));
  renderMoreInfoModal(versionWithCompleteSearchesData);
  fireEvent.click(screen.getByRole("button", { name: /more info/i }));

  // expect(await screen.findByText(/loading synonyms/i)).toBeInTheDocument();
  await waitFor(() => {
    expect(screen.getByText(/no synonyms/i)).toBeInTheDocument();
  });
});

it("shows 'No synonyms' if fetch succeeds but has an error message", async () => {
  // @ts-ignore
  global.fetch = vi.fn(() =>
    Promise.resolve({
      json: () =>
        Promise.resolve({
          error: "an error occurred",
        }),
    }),
  );
  renderMoreInfoModal(versionWithCompleteSearchesData);
  fireEvent.click(screen.getByRole("button", { name: /more info/i }));

  await waitFor(() => {
    expect(screen.getByText(/no synonyms/i)).toBeInTheDocument();
  });
});

it("show 'No synonyms' if the only synonym matches the primary term", async () => {
  // @ts-ignore
  global.fetch = vi.fn(() =>
    Promise.resolve({
      json: () =>
        Promise.resolve({
          synonyms: { "123": ["Test Term"] },
        }),
    }),
  );
  renderMoreInfoModal(versionWithCompleteSearchesData);
  fireEvent.click(screen.getByRole("button", { name: /more info/i }));

  await waitFor(() => {
    expect(screen.getByText(/no synonyms/i)).toBeInTheDocument();
  });
});
