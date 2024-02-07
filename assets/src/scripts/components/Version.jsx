import React from "react";

function Version({ version }) {
  return (
    <li>
      {version.current ? (
        version.tag_or_hash
      ) : (
        <a href={version.url}>{version.tag_or_hash}</a>
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
