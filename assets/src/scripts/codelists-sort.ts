import "../styles/codelist-sort.css";

type AriaSortState = "ascending" | "descending" | "none";
type ActiveAriaSortState = "ascending" | "descending";

/** Read a comparable date value for a grouped tbody from its datetime values */
function getBodyDateSortValue(
  body: HTMLTableSectionElement,
  columnIndex: number,
  direction: ActiveAriaSortState,
): number {
  // Collect every parseable timestamp in this grouped tbody.
  // Some groups have multiple rows (multiple versions), so we inspect each row.
  const values: number[] = [];

  for (const row of Array.from(body.rows)) {
    const cell = row.cells[columnIndex];
    const time = cell.querySelector<HTMLTimeElement>("time[datetime]");
    let rawValue = "";

    // Fallback to text content if datetime is not present
    if (time) {
      rawValue = time.dateTime;
    } else if (cell.textContent) {
      rawValue = cell.textContent.trim();
    }

    const timestamp = Date.parse(rawValue);

    if (!Number.isNaN(timestamp)) {
      values.push(timestamp);
    }
  }

  // If no valid dates exist, force this group to the end for the active direction.
  // Ascending uses +Infinity; descending uses -Infinity.
  if (values.length === 0) {
    if (direction === "ascending") {
      return Infinity;
    }

    return -Infinity;
  }

  // For grouped rows, compare by the earliest date in ascending mode
  // and by the latest date in descending mode.
  if (direction === "ascending") {
    return Math.min(...values);
  }
  return Math.max(...values);
}

/** Sort grouped tbody elements by text in the requested column */
function sortBodiesByText(
  bodies: HTMLTableSectionElement[],
  columnIndex: number,
  direction: ActiveAriaSortState,
): HTMLTableSectionElement[] {
  const bodiesWithSortValues = bodies.map((body, originalIndex) => {
    const firstRow = body.rows[0];
    const cell = firstRow.cells[columnIndex];

    return {
      body,
      originalIndex,
      value: cell.textContent ? cell.textContent.trim() : "",
    };
  });

  bodiesWithSortValues.sort((left, right) => {
    // Negative when the left occurs before right
    // Positive when the right occurs before left
    // Returns 0 if they are equivalent
    const comparison = left.value.localeCompare(right.value, "en-GB", {
      // Whether numeric collation should be used, such that "1" < "2" < "10"
      numeric: true,

      // Only strings that differ in base letters compare as unequal.
      // Examples: a ≠ b, a = á, a = A
      sensitivity: "base",
    });

    // If values compare equal, keep their original order
    if (comparison === 0) {
      return left.originalIndex - right.originalIndex;
    }

    // localeCompare already gives ascending order, so invert it for
    // descending order
    if (direction === "ascending") {
      return comparison;
    } else {
      return comparison * -1;
    }
  });

  return bodiesWithSortValues.map(({ body }) => body);
}

/** Sort grouped tbody elements by datetime values in the requested column */
export function sortBodiesByDate(
  bodies: HTMLTableSectionElement[],
  columnIndex: number,
  direction: ActiveAriaSortState,
): HTMLTableSectionElement[] {
  const bodiesWithSortValues = bodies.map((body, originalIndex) => {
    return {
      body,
      originalIndex,
      value: getBodyDateSortValue(body, columnIndex, direction),
    };
  });

  bodiesWithSortValues.sort((left, right) => {
    if (left.value === right.value) {
      return left.originalIndex - right.originalIndex;
    }

    if (direction === "ascending") {
      return left.value - right.value;
    }

    return right.value - left.value;
  });

  return bodiesWithSortValues.map(({ body }) => body);
}

/** Reorder tbody elements in one DOM write and keep the no-results tbody at the end */
function appendSortedBodies(
  table: HTMLTableElement,
  sortedBodies: HTMLTableSectionElement[],
  noResultsBody: HTMLTableSectionElement | undefined,
) {
  const fragment = document.createDocumentFragment();

  // sortedBodies contains references to the existing <tbody> elements already
  // in the table
  sortedBodies.forEach((body) => {
    // This moves each <tbody> into the DocumentFragment created above
    fragment.append(body);
  });

  if (noResultsBody) {
    // This makes sure the no results <tbody> is at the bottom of the table
    fragment.append(noResultsBody);
  }

  // Move the table elements inside the existing table. A DOM node can only
  // exist in one place at a time, so “old” positions are automatically
  // vacated when the node is appended.
  table.append(fragment);
}

/** Apply sorting for the clicked sort button */
function handleSort(button: HTMLButtonElement) {
  const header = button.closest("th[aria-sort]") as HTMLTableCellElement;
  const table = header.closest("table") as HTMLTableElement;
  const currentSortState = header.ariaSort as AriaSortState;

  const noResultsBody = table.querySelector(
    "[data-codelist-search-no-results-body]",
  ) as HTMLTableSectionElement;
  const sortableBodies = Array.from(table.tBodies).filter((body) => {
    return body !== noResultsBody;
  });

  const direction =
    currentSortState === "ascending" ? "descending" : "ascending";

  header.ariaSort = direction;

  // Set all other header sorts to "none"
  table.querySelectorAll("th[aria-sort]").forEach((th) => {
    if (th !== header) {
      th.ariaSort = "none";
    }
  });

  // Get the column index and the type of sort from the th dataset
  const columnIndex = Number(button.dataset.codelistSortColumn);
  const sortType = button.dataset.codelistSortButton as "string" | "date";
  let sortedBodies: HTMLTableSectionElement[];

  if (sortType === "date") {
    sortedBodies = sortBodiesByDate(sortableBodies, columnIndex, direction);
  } else {
    sortedBodies = sortBodiesByText(sortableBodies, columnIndex, direction);
  }

  appendSortedBodies(table, sortedBodies, noResultsBody);
}

/** Bind sort behavior to all sortable table buttons on the page */
function initCodelistSort() {
  document
    .querySelectorAll<HTMLButtonElement>("[data-codelist-sort-button]")
    .forEach((button) => {
      button.addEventListener("click", () => {
        handleSort(button);
      });
    });
}

initCodelistSort();
