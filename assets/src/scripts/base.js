// Fonts
import "@fontsource/public-sans/400.css";
import "@fontsource/public-sans/500.css";
import "@fontsource/public-sans/600.css";
import "@fontsource/public-sans/700.css";

// jQuery
import jQuery from "jquery/dist/jquery.slim";

// define & and jQuery on the global window object
Object.assign(window, { $: jQuery, jQuery });

// Bootstrap
import "bootstrap";
import "bootstrap/dist/css/bootstrap.css";

// Styles
import "../styles/base.css";

if (document.location.hostname === "www.opencodelists.org") {
  var script = document.createElement("script");
  script.defer = true;
  script.setAttribute("data-domain", "opencodelists.org");
  script.id = "plausible";
  script.src = "https://plausible.io/js/plausible.compat.js";
  document.head.appendChild(script);
}
