import "../styles/base.css";

if (document.location.hostname === "www.opencodelists.org") {
  var script = document.createElement("script");
  script.defer = true;
  script.setAttribute("data-domain", "opencodelists.org");
  script.id = "plausible";
  script.src = "https://plausible.io/js/plausible.compat.js";
  document.head.appendChild(script);
}
