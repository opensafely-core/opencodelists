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
   *   src="https://plausible.io/js/script.pageview-props.tagged-events.js"
   *   event-is_admin="false"
   *   event-is_logged_in="false"
   * ></script>
   */
  const script = document.createElement("script");
  script.defer = true;
  script.setAttribute("data-domain", "opencodelists.org");
  script.src = "https://plausible.io/js/script.pageview-props.tagged-events.js";
  document.head.appendChild(script);

  const isLoggedIn = document.head.querySelector(`meta[name="is_logged_in"]`);
  const isAdmin = document.head.querySelector(`meta[name="is_admin"]`);

  if (isLoggedIn) {
    script.setAttribute("event-is_logged_in", isLoggedIn.content);
  }

  if (isAdmin) {
    script.setAttribute("event-is_admin", isAdmin.content);
  }

  window.plausible =
    window.plausible ||
    function () {
      // biome-ignore lint/suspicious/noAssignInExpressions: Plausible Analytics provided script
      (window.plausible.q = window.plausible.q || []).push(arguments);
    };
}

/**
 * Enable tooltips everywhere
 * https://getbootstrap.com/docs/4.6/components/tooltips/#example-enable-tooltips-everywhere
 */
$(function () {
  $('[data-toggle="tooltip"]').tooltip();
});
