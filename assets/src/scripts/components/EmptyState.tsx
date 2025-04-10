import React from "react";

export default function EmptyState() {
  return (
    <section style={{ maxWidth: "80ch" }}>
      <h2>Create a codelist</h2>
      <p className="lead">
        Search for medical terms or codes to find matching concepts. Then select
        which concepts you want to include in your codelist.
      </p>
      <p>To get started with the search form on the left:</p>
      <ol>
        <li>
          Choose whether to search using a medical term (like "asthma") or a
          specific code
        </li>
        <li>
          Type your search term or code into the search box and click Search
        </li>
        <li>
          The results will show matching concepts organized in a tree structure,
          including any related sub-concepts
        </li>
      </ol>
      <p>
        Your search history will appear below the search box. You can click on
        any previous search to see those results again.
      </p>
      <a href="/docs" target="_blank" rel="noopener noreferrer">
        View the documentation &rarr;
      </a>
    </section>
  );
}
