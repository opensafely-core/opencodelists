// Helper function to check if all search words are included in a given text
const matchesAllWords = (text: string, words: string[]): boolean => {
  return words.every((word) => text.includes(word));
};

// Initializes client-side filtering for the codelists table
const searchCodelistTable = (): void => {
  const searchInput = document.querySelector("[data-codelist-search-input]");
  const searchableCodelistsTable = document.querySelector(
    "[data-codelist-search-table]",
  );
  const tableBody =
    searchableCodelistsTable?.querySelector<HTMLTableSectionElement>("tbody");
  const rows = tableBody?.querySelectorAll<HTMLTableRowElement>(
    "tr:not([data-codelist-search-no-results])",
  );
  const noResultsRow = tableBody?.querySelector<HTMLTableRowElement>(
    "tr[data-codelist-search-no-results]",
  );

  // Return early if the elements we need are not present
  if (
    !(searchInput instanceof HTMLInputElement) ||
    !tableBody ||
    !rows ||
    !noResultsRow
  ) {
    return;
  }

  const searchableRows: Array<{
    row: HTMLTableRowElement;
    searchText: string;
  }> = [];

  rows.forEach((row) => {
    const parts: string[] = [];
    row
      .querySelectorAll<HTMLTableCellElement>("td[data-codelist-search-cell]")
      .forEach((cell) => {
        parts.push(cell.innerText || cell.textContent || "");
      });

    searchableRows.push({
      row,
      searchText: parts.join(" ").toLowerCase(),
    });
  });

  // Applies the current search value to table rows.
  const applyFilter = (): void => {
    const words = searchInput.value
      .toLowerCase()
      .trim()
      .split(/\s+/)
      .filter(Boolean);

    let visibleRowCount = 0;

    searchableRows.forEach(({ row, searchText }) => {
      const isVisible =
        words.length === 0 || matchesAllWords(searchText, words);

      row.classList.toggle("hidden", !isVisible);

      if (isVisible) {
        visibleRowCount += 1;
      }
    });

    if (visibleRowCount === 0) {
      noResultsRow.classList.remove("hidden");
    } else {
      noResultsRow.classList.add("hidden");
    }
  };

  applyFilter();
  searchInput.addEventListener("input", applyFilter);
};

searchCodelistTable();
