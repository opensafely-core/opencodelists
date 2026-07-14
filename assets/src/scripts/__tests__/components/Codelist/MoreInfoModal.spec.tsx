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
  expect(
    screen.queryByRole("button", { name: /icd-10 .* information/i }),
  ).not.toBeInTheDocument();
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

it("shows ICD-10 dagger information in the WHO additional info box", async () => {
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
              },
            },
          }),
      }),
    ),
  );

  const user = userEvent.setup();
  render(
    <MoreInfoModal
      {...props}
      daggerAsteriskInfo={{
        usage: "dagger",
        url: "https://icd.who.int/browse10/2019/en#/A12.3",
      }}
    />,
  );

  await user.click(
    screen.getByRole("button", {
      name: /show icd-10 dagger information for 123/i,
    }),
  );

  expect(await screen.findByText("WHO ICD-10 Additional Info")).toBeVisible();
  expect(screen.getByRole("heading", { name: /usage: dagger/i })).toBeVisible();
  expect(
    screen.getByText(
      "Dagger codes identify the underlying condition; asterisk codes identify the manifestation.",
    ),
  ).toBeVisible();
  expect(
    screen.getByRole("link", {
      name: /view 123 in the who icd-10 browser/i,
    }),
  ).toHaveAttribute("href", "https://icd.who.int/browse10/2019/en#/A12.3");
  expect(
    screen.getByRole("link", {
      name: /read the full dagger\/asterisk guidance \(section 3.1.3 - p20\)/i,
    }),
  ).toBeVisible();
});

it("shows ICD-10 asterisk information without a code-specific browser link", async () => {
  vi.mocked(readValueFromPage).mockReturnValue({ coding_system_id: "icd10" });
  vi.stubGlobal(
    "fetch",
    vi.fn(() =>
      Promise.resolve({
        json: () => Promise.resolve({}),
      }),
    ),
  );

  const user = userEvent.setup();
  render(
    <MoreInfoModal
      {...props}
      daggerAsteriskInfo={{
        usage: "asterisk",
      }}
    />,
  );

  const usageButton = screen.getByRole("button", {
    name: /show icd-10 asterisk information for 123/i,
  });
  expect(usageButton).toHaveTextContent("*");

  await user.click(usageButton);

  expect(
    await screen.findByRole("heading", {
      name: /usage: asterisk/i,
    }),
  ).toBeVisible();
  expect(screen.queryByRole("link", { name: /view 123/i })).toBeNull();
  expect(
    screen.getByRole("link", {
      name: /read the full dagger\/asterisk guidance \(section 3.1.3 - p20\)/i,
    }),
  ).toBeVisible();
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
    await screen.findByRole("heading", { name: "Modifier: Multiple sites" }),
  ).toBeVisible();
  expect(screen.getByText("Includes multiple sites")).toBeVisible();
});

it("uses consistent cards and renders usage after concept and modifier rubrics", async () => {
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
                  inclusion: ["Included condition"],
                  "coding-hint": ["Use an additional code"],
                },
                modifier_rubrics: {
                  "Multiple sites": {
                    note: ["Includes multiple sites"],
                  },
                },
              },
            },
          }),
      }),
    ),
  );

  const user = userEvent.setup();
  render(<MoreInfoModal {...props} daggerAsteriskInfo={{ usage: "dagger" }} />);
  await user.click(screen.getByRole("button", { name: /more info/i }));

  const conceptCard = (
    await screen.findByRole("heading", { name: "Concept: Test Term" })
  ).closest("section") as HTMLElement;
  const modifierCard = screen
    .getByRole("heading", { name: "Modifier: Multiple sites" })
    .closest("section") as HTMLElement;
  const usageCard = screen
    .getByRole("heading", { name: /usage: dagger/i })
    .closest("section") as HTMLElement;
  const codingHint = screen.getByText("Coding hint:");

  for (const card of [conceptCard, modifierCard, usageCard]) {
    expect(card).toHaveClass("builder__additional-info-card");
  }
  expect(conceptCard).toHaveClass("builder__additional-info-card--concept");
  expect(modifierCard).not.toHaveClass(
    "builder__additional-info-card--concept",
    "builder__additional-info-card--usage",
  );
  expect(usageCard).toHaveClass("builder__additional-info-card--usage");
  expect(
    conceptCard.compareDocumentPosition(codingHint) &
      Node.DOCUMENT_POSITION_FOLLOWING,
  ).toBeTruthy();
  expect(
    codingHint.compareDocumentPosition(modifierCard) &
      Node.DOCUMENT_POSITION_FOLLOWING,
  ).toBeTruthy();
  expect(
    modifierCard.compareDocumentPosition(usageCard) &
      Node.DOCUMENT_POSITION_FOLLOWING,
  ).toBeTruthy();
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
                  note: ["Ordered note"],
                  z_kind: ["Generic rubric"],
                  modifierlink: ["Hidden modifier link"],
                  "coding-hint": ["Use additional code"],
                  alpha_kind: ["Alpha rubric"],
                  definition: ["Ordered definition"],
                },
                modifier_rubrics: {},
              },
            },
          }),
      }),
    ),
  );

  const user = userEvent.setup();
  render(<MoreInfoModal {...props} />);
  await user.click(screen.getByRole("button", { name: /more info/i }));

  const alphaHeading = await screen.findByRole("heading", {
    name: "alpha-kind",
  });
  const zHeading = screen.getByRole("heading", { name: "z-kind" });
  const definition = screen.getByText("Ordered definition");
  const note = screen.getByText("Ordered note");
  const conceptCard = screen
    .getByRole("heading", { name: "Concept: Test Term" })
    .closest("section") as HTMLElement;

  expect(within(conceptCard).getByText("Coding hint:")).toBeVisible();
  expect(within(conceptCard).getByText("Use additional code")).toBeVisible();
  expect(within(conceptCard).getByText("Generic rubric")).toBeVisible();
  expect(within(conceptCard).getByText("Alpha rubric")).toBeVisible();
  expect(within(conceptCard).queryByText("Ordered definition")).toBeNull();
  expect(within(conceptCard).queryByText("Ordered note")).toBeNull();
  expect(screen.queryByText("Hidden modifier link")).toBeNull();
  expect(
    definition.compareDocumentPosition(note) & Node.DOCUMENT_POSITION_FOLLOWING,
  ).toBeTruthy();
  expect(
    note.compareDocumentPosition(alphaHeading) &
      Node.DOCUMENT_POSITION_FOLLOWING,
  ).toBeTruthy();
  expect(
    alphaHeading.compareDocumentPosition(zHeading) &
      Node.DOCUMENT_POSITION_FOLLOWING,
  ).toBeTruthy();
});

it("groups non-italic rubrics in a concept box with inclusion and exclusion first", async () => {
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
                  exclusion: ["Excluded condition"],
                  inclusion: ["Included condition"],
                  note: ["Outside the grouped box"],
                  "coding-hint": ["Use an additional code"],
                },
                modifier_rubrics: {},
              },
            },
          }),
      }),
    ),
  );

  const user = userEvent.setup();
  render(<MoreInfoModal {...props} term="Test Term : Multiple sites" />);
  await user.click(screen.getByRole("button", { name: /more info/i }));

  const groupedRubrics = (
    await screen.findByRole("heading", { name: "Concept: Test Term" })
  ).closest("section");
  const note = screen.getByText("Outside the grouped box");
  const codingHint = screen.getByText("Coding hint:");

  expect(groupedRubrics).toHaveClass("builder__additional-info-card");
  expect(
    within(groupedRubrics as HTMLElement).getByText("Includes:"),
  ).toBeVisible();
  expect(
    within(groupedRubrics as HTMLElement).getByText("Included condition"),
  ).toBeVisible();
  expect(
    within(groupedRubrics as HTMLElement).getByText("Excludes:"),
  ).toBeVisible();
  expect(
    within(groupedRubrics as HTMLElement).getByText("Excluded condition"),
  ).toBeVisible();
  expect(
    within(groupedRubrics as HTMLElement).queryByText(
      "Outside the grouped box",
    ),
  ).toBeNull();
  expect(note).toBeVisible();
  expect(
    within(groupedRubrics as HTMLElement).getByText("Use an additional code"),
  ).toBeVisible();
  expect(
    note.compareDocumentPosition(groupedRubrics as HTMLElement) &
      Node.DOCUMENT_POSITION_FOLLOWING,
  ).toBeTruthy();
  expect(
    within(groupedRubrics as HTMLElement)
      .getByText("Excluded condition")
      .compareDocumentPosition(codingHint) & Node.DOCUMENT_POSITION_FOLLOWING,
  ).toBeTruthy();
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
