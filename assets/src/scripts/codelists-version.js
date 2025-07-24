/* v8 ignore start */
// jQuery
import jQuery from "jquery";

// define & and jQuery on the global window object
Object.assign(window, { $: jQuery, jQuery });

// Datatable
import "datatables.net/js/jquery.dataTables.mjs";
import "datatables.net-bs4/js/dataTables.bootstrap4.mjs";
import "datatables.net-bs4/css/dataTables.bootstrap4.css";

$(() => {
  $("#js-codelist-table").DataTable({
    paging: false,
  });

  $('a[data-toggle="tab"]').on("click", function () {
    var url = location.href.split("#")[0];

    if ($(this).attr("href") !== "#about") {
      url += $(this).attr("href");
    }

    history.pushState(null, null, url);
  });

  switchToTab();
});

window.addEventListener("hashchange", switchToTab);

function switchToTab() {
  var hash = location.hash || "#about";
  $('#tab-list a[href="' + hash + '"]').tab("show");
}
/* v8 ignore end */
