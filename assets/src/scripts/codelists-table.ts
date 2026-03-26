/**
 * Returns true when every search word is present in the target text.
 */
const matchesAllWords = (text: string, words: string[]): boolean => {
  return words.every((word) => text.includes(word));
};

/**
 * Initializes client-side filtering for the published codelists table.
 *
 * Filters rows by codelist name and coding system and shows a
 * single fallback row when no codelists match the search query.
 */
const initCodelistsTableFiltering = (): void => {
  const searchInput = document.getElementById("codelist-search");
  const tableBody = document.querySelector<HTMLTableSectionElement>(
    "#published-codelists-table tbody",
  );
  const rows = Array.from(
    tableBody?.querySelectorAll<HTMLTableRowElement>("tr[data-codelist-row]") ??
      [],
  );

  if (
    !(searchInput instanceof HTMLInputElement) ||
    !tableBody ||
    rows.length === 0
  ) {
    return;
  }

  const noResultsRow = document.createElement("tr");
  noResultsRow.setAttribute("data-no-codelists-row", "true");
  noResultsRow.className = "bg-white text-slate-700";
  noResultsRow.innerHTML = `
    <td class="px-3 py-4 pl-4 text-base/snug sm:pl-6" colspan="4">
      No codelists found
    </td>
  `;

  /**
   * Applies the current search value to table rows.
   */
  const applyFilter = (): void => {
    const words = searchInput.value
      .toLowerCase()
      .trim()
      .split(/\s+/)
      .filter(Boolean);
    let visibleRowCount = 0;

    rows.forEach((row) => {
      const searchText = row.dataset.searchText ?? "";
      const isVisible =
        words.length === 0 || matchesAllWords(searchText, words);

      row.classList.toggle("hidden", !isVisible);
      if (isVisible) {
        visibleRowCount += 1;
      }
    });

    if (visibleRowCount === 0) {
      if (!tableBody.querySelector("tr[data-no-codelists-row]")) {
        tableBody.appendChild(noResultsRow);
      }
    } else {
      noResultsRow.remove();
    }
  };

  applyFilter();
  searchInput.addEventListener("input", applyFilter);
};

initCodelistsTableFiltering();
