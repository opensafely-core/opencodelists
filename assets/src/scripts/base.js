/* v8 ignore start */
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
import "@popperjs/core";

import "bootstrap";
import "bootstrap/dist/css/bootstrap.css";

// Lite YouTube Embed
import "lite-youtube-embed/src/lite-yt-embed";
import "lite-youtube-embed/src/lite-yt-embed.css";

// Styles
import "../styles/base.css";

/**
 * Enable tooltips everywhere
 * https://getbootstrap.com/docs/4.6/components/tooltips/#example-enable-tooltips-everywhere
 */
$(() => {
  $('[data-toggle="tooltip"]').tooltip();
});
/* v8 ignore end */
