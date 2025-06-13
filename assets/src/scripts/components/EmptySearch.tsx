import React from "react";

export default function EmptyState() {
  return (
    <section className="max-w-80ch">
      <p className="lead">Your search returned no concepts. You may want to:</p>
      <ol>
        <li>Check your spelling</li>
        <li>Try searching for a similar term</li>
        <li>
          Ensure you have selected the correct option above the search box
          ("Search by code" if searching by code rather than term)
        </li>
      </ol>
      <p>
        If this search was an error, click "Remove" in the "Previous searches"
        box on the left to delete it. If you'd like to record that you performed
        this search but it returned no results, you can leave it as is.
      </p>
    </section>
  );
}
