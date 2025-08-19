/** biome-ignore-all lint/correctness/useUniqueElementIds: IDs required by DOM */
import React from "react";
import type { PageData } from "../../types";

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
  draftURL: PageData["draftURL"];
}

export default function Summary({ counts, draftURL }: SummaryProps) {
  const currentFilter = new URLSearchParams(window.location.search).get(
    "filter",
  );

  const itemHref = (filter: string) =>
    encodeURI(`${draftURL}?filter=${filter}`);

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
            href={encodeURI(draftURL)}
          >
            show all {counts.total} matching concepts
          </a>
        ) : null}
      </div>
    </div>
  );
}
