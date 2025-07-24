/*
 * Interactivity for the codelist table.
 *
 * Each row in the table represents a single codelist. The behaviour changes
 * depending on whether the codelist has one visible version, or multiple
 * visible versions. A codelist can have just a single version when:
 *  - viewing the latest published versions for another user
 *  - if a codelist only has one version
 *  - if filtering the table leads to just one version (e.g. filtering to drafts)
 *
 * When just one version is visible then we want the whole row to highlight on
 * hover, and clicking anywhere in the row open that version. If multiple
 * versions are visible, then the hover behaviour should only occur in the nested
 * table containing the versions.
 *
 * This file has the logic for the above, and for the search box filtering.
 */

// Get all the codelist rows into a data array for future use
const codelistRows = Array.from(
  document.querySelectorAll(".table-codelist > tbody > tr"),
).map((element) => {
  const versionRows = Array.from(element.querySelectorAll("table tr"));
  return {
    element,
    text: element.dataset.codelistText.toLowerCase(),
    datasetId: element.dataset.codelistId,
    versions: versionRows.map((element) => {
      return {
        element,
        text: element.dataset.versionText.toLowerCase(),
      };
    }),
    visibleVersions: versionRows.length,
  };
});

// We apply the search box filtering:
// - on initial page load
// - on the keyup event in the search box
// - if we navigate back to this page and it is loaded from the cache
const searchInputEl = document.getElementById("searchInput");
applyFiltering();
searchInputEl.addEventListener("keyup", () => {
  applyFiltering();
});
window.addEventListener("pageshow", (event) => {
  // Only apply if event.persisted i.e. page load is from a cache
  if (event.persisted) {
    searchInputEl.focus();
    applyFiltering();
  }
});

// Add click handler for rows
codelistRows.forEach((codelistRow) => {
  // Add a click handler for parent row - but only if either no versions (so
  // it's the that_user page), or if only one currently visible version
  codelistRow.element.addEventListener("click", function (e) {
    // Don't trigger if they actually clicked the link
    if (e.target.tagName.toLowerCase() !== "a") {
      if (codelistRow.visibleVersions < 2) {
        // Find and click the link in this row
        const link = this.querySelector("tr:not(.hidden-row) > td > a");
        if (link) link.click();
      }
    }
  });

  codelistRow.versions.forEach((versionRow) => {
    versionRow.element.addEventListener("click", function (e) {
      // Don't trigger if they actually clicked the link
      if (e.target.tagName.toLowerCase() !== "a") {
        // Find and click the link in this row
        const link = this.querySelector("tr:not(.hidden-row) > td > a");
        if (link) link.click();
      }
    });
  });
});

// Helper function to check if all search words are included in a given text
function matchesAllWords(text, words) {
  return words.every((word) => text.includes(word));
}

function applyFiltering() {
  const searchWords = searchInputEl.value.toLowerCase().trim().split(/\s+/);
  codelistRows.forEach((row) => {
    // Does this codelist match all of the words in the search?
    // This matches the "codelist" level attributes (name, coding system, etc.)
    // It does not consider version-specific attributes (draft, under review etc).
    const codelistMatchesSearch = matchesAllWords(row.text, searchWords);

    row.visibleVersions = 0;
    row.versions.forEach((versionRow) => {
      // A version matches if all search words are found in the combined text
      // of the codelist row and the version row.
      const combinedText = `${row.text} ${versionRow.text}`;
      const versionMatchesSearch = matchesAllWords(combinedText, searchWords);

      // If the codelist itself matches, or this specific version matches, show
      // the version row.
      if (codelistMatchesSearch || versionMatchesSearch) {
        versionRow.element.classList.remove("hidden-row");
      }
      if (versionMatchesSearch) {
        row.visibleVersions++;
      } else {
        versionRow.element.classList.add("hidden-row");
      }
    });

    if (codelistMatchesSearch || row.visibleVersions > 0) {
      // Display the main codelist row if its own text matches the search, or
      // if any of its versions are visible after filtering.
      row.element.classList.remove("hidden-row");
    } else {
      row.element.classList.add("hidden-row");
    }

    // Add/remove class for styling based on the number of visible versions.
    if (row.visibleVersions < 2) {
      row.element.classList.add("single-version-row");
    } else {
      row.element.classList.remove("single-version-row");
    }
  });
}
