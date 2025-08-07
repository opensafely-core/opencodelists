import React from "react";
import { readValueFromPage } from "../../_utils";

export interface VersionProps {
  created_at: string;
  current: boolean;
  status: string;
  tag_or_hash: string;
  url: string;
}

function Version({ version }: { version: VersionProps }) {
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
    >
      <div className="d-flex justify-content-between align-items-center">
        <span className="d-block text-monospace font-weight-bold">
          {version.current ? (
            version.tag_or_hash
          ) : (
            <a href={encodeURI(version.url)}>{version.tag_or_hash}</a>
          )}
        </span>
        {version.status === "draft" && (
          <span className="badge badge-light">Draft</span>
        )}
        {version.status === "under review" && (
          <span className="badge badge-info">Under review</span>
        )}
        {version.status === "published" && (
          <span className="badge badge-success">Published</span>
        )}
      </div>
      <div className="created d-block p-0 mt-1">
        <span className="font-weight-bold">Added to OpenCodelists</span>
        <span className="d-block">
          {createdDate} at {createdTime}
        </span>
      </div>
    </li>
  );
}

export default function Versions() {
  const versions: VersionProps[] = readValueFromPage("versions");

  if (!versions?.length) return null;

  return (
    <div className="card">
      <h2 className="card-header h6 font-weight-bold">Versions</h2>
      <ol className="list-group list-group-flush sidebar-versions">
        {versions.map((version) => (
          <Version key={version.tag_or_hash} version={version} />
        ))}
      </ol>
    </div>
  );
}
