import "@zachleat/details-utils";

import "../styles/feedback-form.css";

const feedbackForm = document.getElementById("feedbackForm");
if (feedbackForm) {
  // Example code
  const summary = feedbackForm.querySelector("summary");
  summary.classList.add("feedback-form__summary");
}
