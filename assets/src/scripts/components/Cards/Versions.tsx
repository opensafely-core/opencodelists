import React from "react";
import {
  Badge,
  Card,
  ListGroup,
  OverlayTrigger,
  Tooltip,
} from "react-bootstrap";
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
    <ListGroup.Item
      as="li"
      key={version.tag_or_hash}
      variant={version.current ? "secondary" : undefined}
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
          <Badge variant="light">Draft</Badge>
        ) : null}
        {version.status === "under review" ? (
          <Badge variant="info">Under review</Badge>
        ) : null}
        {version.status === "published" ? (
          <Badge variant="success">Published</Badge>
        ) : null}
      </div>
      <span className="created d-block p-0">
        <OverlayTrigger
          placement="right"
          overlay={
            <Tooltip id={version.tag_or_hash}>
              When this codelist version was added to OpenCodelists
            </Tooltip>
          }
        >
          <abbr className="font-weight-bold">Created</abbr>
        </OverlayTrigger>
        : {createdDate} at {createdTime}
      </span>
    </ListGroup.Item>
  );
}

export default function Versions() {
  const versions: VersionProps[] = readValueFromPage("versions");

  if (!versions?.length) return null;

  return (
    <Card>
      <Card.Header as="h2" className="h6 font-weight-bold">
        Versions
      </Card.Header>
      <ListGroup variant="flush" className="sidebar-versions" as="ol">
        {versions.map((version) => (
          <Version key={version.tag_or_hash} version={version} />
        ))}
      </ListGroup>
    </Card>
  );
}
