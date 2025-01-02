import React from "react";

export interface VersionProps {
  version: {
    current: boolean,
    status: string,
    tag_or_hash: string,
    url: string,
  }
}

function Version({ version }: VersionProps) {
  return (
    <li>
      {version.current ? (
        version.tag_or_hash
      ) : (
        <a href={encodeURI(version.url)}>{version.tag_or_hash}</a>
      )}

      {version.status === "draft" ? (
        <>
          {" "}
          <span className="badge badge-primary">Draft</span>
        </>
      ) : null}

      {version.status === "under review" ? (
        <>
          {" "}
          <span className="badge badge-primary">Review</span>
        </>
      ) : null}
    </li>
  );
}

export default Version;
