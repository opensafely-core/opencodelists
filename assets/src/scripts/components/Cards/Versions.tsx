import React from "react";
import { readValueFromPage } from "../../_utils";
import { VERSIONS } from "../../types";

function Version({ version }: { version: VERSIONS[number] }) {
  const createdAt = new Date(version.created_at);
  const userTimeZone =
    Intl?.DateTimeFormat()?.resolvedOptions()?.timeZone || "UTC";
  const userLang = navigator?.language || "en-GB";

  const createdDate = createdAt.toLocaleDateString(userLang, {
    day: "numeric",
    month: "short",
    year: "numeric",
    timeZone: userTimeZone,
  });

  const createdTime = createdAt.toLocaleTimeString(userLang, {
    hour: "2-digit",
    minute: "2-digit",
    timeZone: userTimeZone,
  });

  return (
    <li
      className={`list-group-item ${version.current ? "list-group-item-secondary" : ""}`}
      key={version.tag_or_hash}
    >
      <div className="d-flex justify-content-between align-items-center">
        <span className="d-block text-monospace font-weight-bold">
          {version.current ? (
            version.tag_or_hash
          ) : (
            <a href={encodeURI(version.url)}>{version.tag_or_hash}</a>
          )}
        </span>
        {version.status === "draft" ? (
          <span className="badge badge-light">Draft</span>
        ) : null}
        {version.status === "under review" ? (
          <span className="badge badge-info">Under review</span>
        ) : null}
        {version.status === "published" ? (
          <span className="badge badge-success">Published</span>
        ) : null}
      </div>
      <span className="created d-block p-0">
        Added to the site on
        <br />
        {createdDate} at {createdTime}
      </span>
    </li>
  );
}

export default function Versions() {
  const versions: VERSIONS = readValueFromPage("versions");

  if (!versions?.length) return null;

  return (
    <div className="card">
      <div className="h6 font-weight-bold card-header">Versions</div>
      <ol className="sidebar-versions list-group list-group-flush">
        {versions.map((version) => (
          <Version key={version.tag_or_hash} version={version} />
        ))}
      </ol>
    </div>
  );
}
