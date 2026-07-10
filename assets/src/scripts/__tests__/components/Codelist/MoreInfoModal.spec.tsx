import "@testing-library/jest-dom";
import { act, render, screen, waitFor, within } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import React from "react";
import { afterEach, beforeEach, expect, it, vi } from "vitest";
import Hierarchy from "../../../_hierarchy";
import { getCookie, readValueFromPage } from "../../../_utils";
import MoreInfoModal from "../../../components/Codelist/MoreInfoModal";
import type { Status } from "../../../types";
import * as versionWithCompleteSearchesData from "../../fixtures/version_with_complete_searches.json";

// Mock dependencies
vi.mock("../../../_utils", () => ({
  getCookie: vi.fn(() => "test-csrf-token"),
  readValueFromPage: vi.fn(() => ({ coding_system_id: "snomedct" })),
}));

beforeEach(() => {
  vi.mocked(readValueFromPage).mockReturnValue({
    coding_system_id: "snomedct",
  });
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

it.each([
  ["-", { target: "-" }, "Excluded"],
  ["?", { target: "?" }, "Unresolved"],
  [
    "(+)",
    { includedAncestor: "+", excludedAncestor: "?", target: "(+)" },
    'Included because you included its ancestor: "Included ancestor [includedAncestor]"',
  ],
  [
    "(-)",
    { includedAncestor: "?", excludedAncestor: "-", target: "(-)" },
    'Excluded because you excluded its ancestor: "Excluded ancestor [excludedAncestor]"',
  ],
  [
    "!",
    { includedAncestor: "+", excludedAncestor: "-", target: "!" },
    'In conflict!  Included by "Included ancestor [includedAncestor]", and excluded by "Excluded ancestor [excludedAncestor]"',
  ],
] as const)("shows status text for %s status", async (status, codeToStatus, expectedText) => {
  const user = userEvent.setup();
  const hierarchy = new Hierarchy(
    {
      target: ["includedAncestor", "excludedAncestor"],
    },
    {
      includedAncestor: ["target"],
      excludedAncestor: ["target"],
    },
  );

  render(
    <MoreInfoModal
      allCodes={["includedAncestor", "excludedAncestor", "target"]}
      code="target"
      codeToStatus={codeToStatus}
      codeToTerm={{
        includedAncestor: "Included ancestor",
        excludedAncestor: "Excluded ancestor",
        target: "Target term",
      }}
      hierarchy={hierarchy}
      status={status}
      term="Target term"
    />,
  );
  await user.click(screen.getByRole("button", { name: /more info/i }));

  expect(
    await screen.findByText(
      (_, element) => element?.textContent === expectedText,
    ),
  ).toBeVisible();
});

it("shows clinically equivalent ICD-10 description differences in a green box", async () => {
  vi.mocked(readValueFromPage).mockReturnValue({ coding_system_id: "icd10" });
  vi.stubGlobal(
    "fetch",
    vi.fn(() =>
      Promise.resolve({
        json: () =>
          Promise.resolve({
            term_differences: {
              "123": {
                combined_2016: "NHS description",
                who_2019: "WHO description",
                equivalent: true,
              },
            },
          }),
      }),
    ),
  );

  const user = userEvent.setup();
  render(<MoreInfoModal {...props} />);
  await user.click(screen.getByRole("button", { name: /more info/i }));

  const descriptionSection = (
    await screen.findByText("ICD-10 Edition Descriptions")
  ).closest("section");
  expect(descriptionSection).toHaveClass("border-success");

  expect(
    screen.getByText("The description of 123 differs", { exact: false }),
  ).toBeVisible();
  expect(
    screen.getByText("We consider these terms clinically equivalent", {
      exact: false,
    }),
  ).toBeVisible();
  expect(screen.getByText("NHS description")).toBeVisible();
  expect(screen.getByText("WHO description")).toBeVisible();
});

it("shows clinically different ICD-10 description differences in a red box", async () => {
  vi.mocked(readValueFromPage).mockReturnValue({ coding_system_id: "icd10" });
  vi.stubGlobal(
    "fetch",
    vi.fn(() =>
      Promise.resolve({
        json: () =>
          Promise.resolve({
            term_differences: {
              "123": {
                combined_2016: "NHS description",
                who_2019: "WHO description",
                equivalent: false,
              },
            },
          }),
      }),
    ),
  );

  const user = userEvent.setup();
  render(<MoreInfoModal {...props} />);
  await user.click(screen.getByRole("button", { name: /more info/i }));

  const descriptionSection = (
    await screen.findByText("ICD-10 Edition Descriptions")
  ).closest("section");
  expect(descriptionSection).toHaveClass("border-danger");
  expect(
    screen.getByText("The description of 123 differs", { exact: false }),
  ).toBeVisible();
  expect(
    screen.getByText("We consider these terms different", { exact: false }),
  ).toBeVisible();
  expect(screen.getByText("NHS description")).toBeVisible();
  expect(screen.getByText("WHO description")).toBeVisible();
});

it("shows ICD-10 rubric information from ancestor codes", async () => {
  vi.mocked(readValueFromPage).mockReturnValue({ coding_system_id: "icd10" });
  vi.stubGlobal(
    "fetch",
    vi.fn(() =>
      Promise.resolve({
        json: () =>
          Promise.resolve({
            rubrics: {
              "123": {
                concept_rubrics: {
                  inclusion: ["Current-code inclusion"],
                },
                modifier_rubrics: {},
                ancestor_rubrics: [
                  {
                    code: "12",
                    term: "Parent code",
                    concept_rubrics: {
                      exclusion: ["Parent-code exclusion"],
                    },
                    modifier_rubrics: {},
                  },
                ],
              },
            },
          }),
      }),
    ),
  );

  const user = userEvent.setup();
  render(<MoreInfoModal {...props} />);
  await user.click(screen.getByRole("button", { name: /more info/i }));

  expect(
    await screen.findByRole("heading", {
      name: /from higher up the icd-10 tree/i,
    }),
  ).toBeVisible();
  expect(screen.getByText("Current-code inclusion")).toBeVisible();
  expect(screen.getByText("Parent code (12)")).toBeVisible();
  expect(screen.getByText("Parent-code exclusion")).toBeVisible();
  expect(screen.queryByRole("heading", { name: /synonyms/i })).toBeNull();
});

it("shows ICD-10 modifier rubric information", async () => {
  vi.mocked(readValueFromPage).mockReturnValue({ coding_system_id: "icd10" });
  vi.stubGlobal(
    "fetch",
    vi.fn(() =>
      Promise.resolve({
        json: () =>
          Promise.resolve({
            rubrics: {
              "123": {
                concept_rubrics: {},
                modifier_rubrics: {
                  "Multiple sites": {
                    note: ["Includes multiple sites"],
                  },
                },
                ancestor_rubrics: [],
              },
            },
          }),
      }),
    ),
  );

  const user = userEvent.setup();
  render(<MoreInfoModal {...props} />);
  await user.click(screen.getByRole("button", { name: /more info/i }));

  expect(
    await screen.findByRole("heading", { name: 'Modifier: "Multiple sites"' }),
  ).toBeVisible();
  expect(screen.getByText("Includes multiple sites")).toBeVisible();
});

it("handles ICD-10 rubrics with omitted optional fields", async () => {
  vi.mocked(readValueFromPage).mockReturnValue({ coding_system_id: "icd10" });
  vi.stubGlobal(
    "fetch",
    vi.fn(() =>
      Promise.resolve({
        json: () =>
          Promise.resolve({
            rubrics: {
              "123": {
                concept_rubrics: {
                  inclusion: ["Rubric without optional fields"],
                },
              },
            },
          }),
      }),
    ),
  );

  const user = userEvent.setup();
  render(<MoreInfoModal {...props} />);
  await user.click(screen.getByRole("button", { name: /more info/i }));

  expect(
    await screen.findByText("Rubric without optional fields"),
  ).toBeVisible();
});

it("formats, filters, and orders ICD-10 rubric kinds", async () => {
  vi.mocked(readValueFromPage).mockReturnValue({ coding_system_id: "icd10" });
  vi.stubGlobal(
    "fetch",
    vi.fn(() =>
      Promise.resolve({
        json: () =>
          Promise.resolve({
            rubrics: {
              "123": {
                concept_rubrics: {
                  z_kind: ["Generic rubric"],
                  modifierlink: ["Hidden modifier link"],
                  "coding-hint": ["Use additional code"],
                  inclusion: ["Preferred rubric"],
                  alpha_kind: ["Alpha rubric"],
                },
                modifier_rubrics: {},
                ancestor_rubrics: [],
              },
            },
          }),
      }),
    ),
  );

  const user = userEvent.setup();
  render(<MoreInfoModal {...props} />);
  await user.click(screen.getByRole("button", { name: /more info/i }));

  const includesHeading = await screen.findByRole("heading", {
    name: "Includes:",
  });
  const alphaHeading = screen.getByRole("heading", { name: "alpha-kind" });
  const zHeading = screen.getByRole("heading", { name: "z-kind" });

  expect(screen.getByText("Preferred rubric")).toBeVisible();
  expect(screen.getByText("Coding hint:")).toBeVisible();
  expect(screen.getByText("Use additional code")).toBeVisible();
  expect(screen.getByText("Generic rubric")).toBeVisible();
  expect(screen.queryByText("Hidden modifier link")).toBeNull();
  expect(
    includesHeading.compareDocumentPosition(alphaHeading) &
      Node.DOCUMENT_POSITION_FOLLOWING,
  ).toBeTruthy();
  expect(
    alphaHeading.compareDocumentPosition(zHeading) &
      Node.DOCUMENT_POSITION_FOLLOWING,
  ).toBeTruthy();
});

it("shows ICD-10 chapter ancestors with chapter label", async () => {
  vi.mocked(readValueFromPage).mockReturnValue({ coding_system_id: "icd10" });
  vi.stubGlobal(
    "fetch",
    vi.fn(() =>
      Promise.resolve({
        json: () =>
          Promise.resolve({
            rubrics: {
              "123": {
                concept_rubrics: {},
                modifier_rubrics: {},
                ancestor_rubrics: [
                  {
                    code: "XIII",
                    term: "Diseases of the musculoskeletal system",
                    concept_rubrics: {
                      inclusion: ["Chapter inclusion"],
                    },
                    modifier_rubrics: {},
                  },
                ],
              },
            },
          }),
      }),
    ),
  );

  const user = userEvent.setup();
  render(<MoreInfoModal {...props} />);
  await user.click(screen.getByRole("button", { name: /more info/i }));

  expect(
    await screen.findByRole("heading", {
      name: /Diseases of the musculoskeletal system.*Chapter XIII/i,
    }),
  ).toBeVisible();
});

it("does not show the ICD-10 rubric section when no rubrics are returned", async () => {
  vi.mocked(readValueFromPage).mockReturnValue({ coding_system_id: "icd10" });
  vi.stubGlobal(
    "fetch",
    vi.fn(() =>
      Promise.resolve({
        json: () =>
          Promise.resolve({
            rubrics: {
              "123": {
                concept_rubrics: {},
                modifier_rubrics: {},
                ancestor_rubrics: [],
              },
            },
          }),
      }),
    ),
  );

  const user = userEvent.setup();
  render(<MoreInfoModal {...props} />);
  await user.click(screen.getByRole("button", { name: /more info/i }));

  expect(await screen.findByText("Included")).toBeVisible();
  expect(screen.queryByText("WHO ICD-10 Additional Info")).toBeNull();
});

it("does not show the ICD-10 rubric section when rubric fields are omitted", async () => {
  vi.mocked(readValueFromPage).mockReturnValue({ coding_system_id: "icd10" });
  vi.stubGlobal(
    "fetch",
    vi.fn(() =>
      Promise.resolve({
        json: () =>
          Promise.resolve({
            rubrics: {
              "123": {},
            },
          }),
      }),
    ),
  );

  const user = userEvent.setup();
  render(<MoreInfoModal {...props} />);
  await user.click(screen.getByRole("button", { name: /more info/i }));

  expect(await screen.findByText("Included")).toBeVisible();
  expect(screen.queryByText("WHO ICD-10 Additional Info")).toBeNull();
});

it("shows ICD-10 ancestor rubrics when the current code has no own rubrics", async () => {
  vi.mocked(readValueFromPage).mockReturnValue({ coding_system_id: "icd10" });
  vi.stubGlobal(
    "fetch",
    vi.fn(() =>
      Promise.resolve({
        json: () =>
          Promise.resolve({
            rubrics: {
              "123": {
                concept_rubrics: {},
                ancestor_rubrics: [
                  {
                    code: "12",
                    term: "Parent code",
                    concept_rubrics: {
                      inclusion: ["Ancestor-only inclusion"],
                    },
                    modifier_rubrics: {},
                  },
                ],
              },
            },
          }),
      }),
    ),
  );

  const user = userEvent.setup();
  render(<MoreInfoModal {...props} />);
  await user.click(screen.getByRole("button", { name: /more info/i }));

  expect(await screen.findByText("Ancestor-only inclusion")).toBeVisible();
  expect(screen.queryByRole("heading", { name: /for this code/i })).toBeNull();
});

it("closes the modal", async () => {
  const user = userEvent.setup();
  render(<MoreInfoModal {...props} />);
  await user.click(screen.getByRole("button", { name: /more info/i }));

  expect(await screen.findByRole("dialog")).toBeVisible();
  await user.click(screen.getByRole("button", { name: /close/i }));

  await waitFor(() => {
    expect(screen.queryByRole("dialog")).toBeNull();
  });
});

it("does not refetch loaded more-info data when reopened", async () => {
  const fetch = vi.fn((_: string, __: RequestInit) =>
    Promise.resolve({
      json: () =>
        Promise.resolve({
          synonyms: { "123": ["Alpha"] },
          references: { "123": [] },
        }),
    }),
  );
  vi.stubGlobal("fetch", fetch);

  const user = userEvent.setup();
  render(<MoreInfoModal {...props} />);
  await user.click(screen.getByRole("button", { name: /more info/i }));
  expect(await screen.findByText("Alpha")).toBeVisible();
  await user.click(screen.getByRole("button", { name: /close/i }));
  await waitFor(() => {
    expect(screen.queryByRole("dialog")).toBeNull();
  });

  await user.click(screen.getByRole("button", { name: /more info/i }));

  expect(await screen.findByText("Alpha")).toBeVisible();
  expect(fetch).toHaveBeenCalledTimes(1);
});

it("fetches more-info data without a CSRF header when there is no cookie", async () => {
  vi.mocked(getCookie).mockReturnValue(undefined);
  const fetch = vi.fn((_: string, __: RequestInit) =>
    Promise.resolve({
      json: () =>
        Promise.resolve({
          synonyms: { "123": [] },
          references: { "123": [] },
        }),
    }),
  );
  vi.stubGlobal("fetch", fetch);

  const user = userEvent.setup();
  render(<MoreInfoModal {...props} />);
  await user.click(screen.getByRole("button", { name: /more info/i }));

  expect(await screen.findByText(/no synonyms/i)).toBeVisible();
  const headers = fetch.mock.calls[0][1].headers as Headers;
  expect(headers.has("X-CSRFToken")).toBe(false);
});
