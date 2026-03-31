import "@testing-library/jest-dom";
import { screen } from "@testing-library/dom";
import userEvent from "@testing-library/user-event";
import { beforeEach, describe, expect, it, vi } from "vitest";

const loadScript = async () => {
  await import("../codelists-table");
};

const getSearchInput = (): HTMLInputElement => {
  const searchInput = screen.getByRole("searchbox", {
    name: "Search codelists",
  });

  if (!(searchInput instanceof HTMLInputElement)) {
    throw new Error("Expected search input to be an HTMLInputElement");
  }

  return searchInput;
};

describe("codelists-table", () => {
  beforeEach(() => {
    vi.resetModules();
    document.body.innerHTML = "";
  });

  it("filters on module init and on subsequent input events", async () => {
    document.body.innerHTML = `
    <label for="codelist-search">Search codelists</label>
    <input id="codelist-search" data-codelist-search-input type="search" />
    <table data-codelist-search-table>
      <tbody>
        <tr>
          <td data-codelist-search-cell>Asthma</td>
          <td data-codelist-search-cell>SNOMED</td>
          <td>8 codes</td>
          <td>01 Jan 2026</td>
        </tr>
        <tr>
          <td data-codelist-search-cell>Breathlessness</td>
          <td data-codelist-search-cell>dm+d</td>
          <td>12 codes</td>
          <td>04 Feb 2026</td>
        </tr>
        <tr>
          <td data-codelist-search-cell>Dyspnea</td>
          <td data-codelist-search-cell>CTV3</td>
          <td>12 codes</td>
          <td>04 Feb 2026</td>
        </tr>
        <tr class="hidden bg-white text-slate-700" data-codelist-search-no-results>
          <td colspan="4">No codelists found</td>
        </tr>
      </tbody>
    </table>
  `;

    await loadScript();
    const user = userEvent.setup();
    const searchInput = getSearchInput();

    expect(
      screen.getByRole("cell", { name: "Asthma" }).parentElement,
    ).not.toHaveClass("hidden");
    expect(
      screen.getByRole("cell", { name: "Breathlessness" }).parentElement,
    ).not.toHaveClass("hidden");
    expect(
      screen.getByRole("cell", { name: "Dyspnea" }).parentElement,
    ).not.toHaveClass("hidden");
    expect(screen.getByRole("row", { name: "No codelists found" })).toHaveClass(
      "hidden",
    );

    await user.type(searchInput, " not a match   ");

    expect(
      screen.getByRole("cell", { name: "Asthma" }).parentElement,
    ).toHaveClass("hidden");
    expect(
      screen.getByRole("cell", { name: "Breathlessness" }).parentElement,
    ).toHaveClass("hidden");
    expect(
      screen.getByRole("cell", { name: "Dyspnea" }).parentElement,
    ).toHaveClass("hidden");
    expect(
      screen.getByRole("row", { name: "No codelists found" }),
    ).not.toHaveClass("hidden");

    await user.clear(searchInput);

    expect(
      screen.getByRole("cell", { name: "Asthma" }).parentElement,
    ).not.toHaveClass("hidden");
    expect(
      screen.getByRole("cell", { name: "Breathlessness" }).parentElement,
    ).not.toHaveClass("hidden");
    expect(
      screen.getByRole("cell", { name: "Dyspnea" }).parentElement,
    ).not.toHaveClass("hidden");
    expect(screen.getByRole("row", { name: "No codelists found" })).toHaveClass(
      "hidden",
    );

    await user.type(searchInput, " Breathless   ");

    expect(
      screen.getByRole("cell", { name: "Asthma" }).parentElement,
    ).toHaveClass("hidden");
    expect(
      screen.getByRole("cell", { name: "Breathlessness" }).parentElement,
    ).not.toHaveClass("hidden");
    expect(
      screen.getByRole("cell", { name: "Dyspnea" }).parentElement,
    ).toHaveClass("hidden");
    expect(screen.getByRole("row", { name: "No codelists found" })).toHaveClass(
      "hidden",
    );
  });

  it("returns early when required DOM elements are missing", async () => {
    document.body.innerHTML = "<p>No table on this page</p>";

    await expect(loadScript()).resolves.toBeUndefined();
  });

  it("filters using text from searchable cells", async () => {
    document.body.innerHTML = `
    <label for="codelist-search">Search codelists</label>
    <input id="codelist-search" data-codelist-search-input type="search" />
    <table data-codelist-search-table>
      <tbody>
        <tr>
          <td data-codelist-search-cell></td>
          <td data-codelist-search-cell>SNOMED</td>
          <td>8 codes</td>
          <td>01 Jan 2026</td>
        </tr>
        <tr>
          <td data-codelist-search-cell>Breathlessness</td>
          <td data-codelist-search-cell>dm+d</td>
          <td>12 codes</td>
          <td>04 Feb 2026</td>
        </tr>
        <tr>
          <td data-codelist-search-cell>Dyspnea</td>
          <td data-codelist-search-cell>CTV3</td>
          <td>12 codes</td>
          <td>04 Feb 2026</td>
        </tr>
        <tr class="hidden bg-white text-slate-700" data-codelist-search-no-results>
          <td colspan="4">No codelists found</td>
        </tr>
      </tbody>
    </table>
  `;

    await loadScript();
    const user = userEvent.setup();
    const searchInput = getSearchInput();
    await user.type(searchInput, "snomed");

    expect(
      screen.getByRole("cell", { name: "SNOMED" }).parentElement,
    ).not.toHaveClass("hidden");
    expect(
      screen.getByRole("cell", { name: "Breathlessness" }).parentElement,
    ).toHaveClass("hidden");
    expect(
      screen.getByRole("cell", { name: "Dyspnea" }).parentElement,
    ).toHaveClass("hidden");
    expect(screen.getByRole("row", { name: "No codelists found" })).toHaveClass(
      "hidden",
    );
  });
});
