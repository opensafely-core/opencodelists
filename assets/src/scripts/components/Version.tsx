import React from "react";
import { Badge } from "react-bootstrap";
import { VersionT } from "../types";

interface VersionProps {
  version: VersionT;
}

export default function Version({ version }: VersionProps) {
  return (
    <li>
      {version.current ? (
        version.tag_or_hash
      ) : (
        <a href={encodeURI(version.url)}>{version.tag_or_hash}</a>
      )}

      {version.status === "draft" ? (
        <Badge className="ml-1" variant="primary">
          Draft
        </Badge>
      ) : null}

      {version.status === "under review" ? (
        <Badge className="ml-1" variant="primary">
          Review
        </Badge>
      ) : null}
    </li>
  );
}
