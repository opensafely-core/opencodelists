import "../styles/codelist-sort.css";

const SORTABLE_BUTTON_SELECTOR = "[data-codelist-sort-button]";
const SORTABLE_HEADER_SELECTOR = "th[aria-sort]";

document.addEventListener("click", (event) => {
  const target = event.target;
  if (!(target instanceof Element)) {
    return;
  }

  const button = target.closest<HTMLButtonElement>(SORTABLE_BUTTON_SELECTOR);
  if (!button) {
    return;
  }

  const header = button.closest<HTMLTableCellElement>(SORTABLE_HEADER_SELECTOR);
  if (!header) {
    return;
  }

  const table = header.closest("table");
  if (!table) {
    return;
  }

  table
    .querySelectorAll<HTMLTableCellElement>(SORTABLE_HEADER_SELECTOR)
    .forEach((otherHeader) => {
      if (otherHeader !== header && otherHeader.ariaSort !== "none") {
        otherHeader.ariaSort = "none";
      }
    });

  header.ariaSort =
    header.ariaSort === "ascending" ? "descending" : "ascending";
});
