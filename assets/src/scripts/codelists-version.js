/* v8 ignore start */
// jQuery
import jQuery from "jquery";

// define & and jQuery on the global window object
Object.assign(window, { $: jQuery, jQuery });

// Datatable
// biome-ignore lint/correctness/noUndeclaredDependencies: legacy datatable plugin
import "datatables.net/js/jquery.dataTables.mjs";
import "datatables.net-bs4/js/dataTables.bootstrap4.mjs";
import "datatables.net-bs4/css/dataTables.bootstrap4.css";

$(() => {
  $("#js-codelist-table").DataTable({
    paging: false,
  });
});
/* v8 ignore end */

const tabList = document.getElementById("tab-list");
const tabNavButtons = tabList?.querySelectorAll(`button[data-toggle="tab"]`);

function setActiveTab(hash) {
  // Show tab via Bootstrap's tab API
  $(tabList).find(`[data-target="${hash}"]`).tab("show");

  // Reset all tab button styles
  tabNavButtons.forEach((btn) => {
    btn.classList.remove("active");
    btn.classList.add("text-primary");
  });

  // Activate the correct tab button
  const activeBtn = tabList.querySelector(`[data-target="${hash}"]`);
  if (activeBtn) {
    activeBtn.classList.add("active");
    activeBtn.classList.remove("text-primary");
  }
}

function switchToTab() {
  setActiveTab(location.hash || "#about");
}

if (tabList && tabNavButtons.length) {
  // Initialize on page load
  switchToTab();

  // Handle clicks + pushState
  tabNavButtons.forEach((btn) => {
    btn.addEventListener("click", () => {
      const baseUrl = location.origin + location.pathname;
      const tabUrl = btn.dataset.target;
      history.pushState(
        null,
        null,
        tabUrl !== "#about" ? baseUrl + tabUrl : baseUrl,
      );
      setActiveTab(tabUrl);
    });
  });

  // Handle back/forward navigation
  window.addEventListener("hashchange", switchToTab);
}
