import React from "react";

export default function EmptyState() {
  return (
    <section style={{ maxWidth: "80ch" }}>
      <p className="lead">Your search returned no concepts. You may want to:</p>
      <ol>
        <li>Double check the spelling</li>
        <li>
          Make sure that if you're searching for a code (rather than a search
          term) that you have selected the correct option ("Search by code"
          above the search box on the left)
        </li>
        <li>Try searching for a similar term</li>
      </ol>
      <p>
        If this search was an error, you can click "Remove" from the "Previous
        searches" box on the left to get rid of it. However, if you want other
        people to know that you tried this search, but it returned no results,
        then you can leave it as a blank search.
      </p>
    </section>
  );
}
