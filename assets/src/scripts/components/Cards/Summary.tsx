import React from "react";
import { readValueFromPage } from "../../_utils";
import type { BUILDER_CONFIG } from "../../types";

export interface SummaryProps {
  counts: {
    "!": number;
    "(+)": number;
    "(-)": number;
    "+": number;
    "-": number;
    "?": number;
    total: number;
  };
}

export default function Summary({ counts }: SummaryProps) {
  const { url }: BUILDER_CONFIG = readValueFromPage("builder-config");
  const currentFilter = new URLSearchParams(window.location.search).get(
    "filter",
  );

  const itemHref = (filter: string) =>
    encodeURI(`${url.draft}?filter=${filter}`);

  return (
    <div className="card">
      <h2 className="card-header h6 font-weight-bold">
        Concepts found ({counts.total})
      </h2>
      <div className="list-group list-group-flush">
        {counts["+"] > 0 && (
          <a
            className={`list-group-item list-group-item-action ${currentFilter === "included" ? "active" : ""}`}
            href={itemHref("included")}
            id="summary-included"
          >
            {counts["+"] + counts["(+)"]} included concepts
          </a>
        )}
        {counts["-"] > 0 && (
          <a
            className={`list-group-item list-group-item-action ${currentFilter === "excluded" ? "active" : ""}`}
            href={itemHref("excluded")}
            id="summary-excluded"
          >
            {counts["-"] + counts["(-)"]} excluded concepts
          </a>
        )}
        {counts["?"] > 0 && (
          <a
            className={`list-group-item list-group-item-action ${currentFilter === "unresolved" ? "active" : ""}`}
            href={itemHref("unresolved")}
            id="summary-unresolved"
          >
            {counts["?"]} unresolved concepts
          </a>
        )}
        {counts["!"] > 0 && (
          <a
            className={`list-group-item list-group-item-action ${currentFilter === "in-conflict" ? "active" : ""}`}
            href={itemHref("in-conflict")}
            id="summary-in-conflict"
          >
            {counts["!"]} conflicted concepts
          </a>
        )}
        {currentFilter ? (
          <a
            className="list-group-item list-group-item-action font-italic"
            href={encodeURI(url.draft)}
          >
            show all {counts.total} matching concepts
          </a>
        ) : null}
      </div>
    </div>
  );
}
