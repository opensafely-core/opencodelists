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

// Lite YouTube Embed
import "lite-youtube-embed/src/lite-yt-embed";
import "lite-youtube-embed/src/lite-yt-embed.css";

// Styles
import "../styles/base.css";

if (document.location.hostname === "www.opencodelists.org") {
  /**
   * <script
   *   defer
   *   data-domain="opencodelists.org"
   *   src="https://plausible.io/js/script.js"
   * ></script>
   */
  const script = document.createElement("script");
  script.defer = true;
  script.setAttribute("data-domain", "opencodelists.org");
  script.src = "https://plausible.io/js/script.js";
  document.head.appendChild(script);

  window.plausible =
    window.plausible ||
    function () {
      (window.plausible.q = window.plausible.q || []).push(arguments);
    };
}
