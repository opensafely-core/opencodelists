import React from "react";
import { Badge, Card, ListGroup } from "react-bootstrap";
import { VersionT } from "../types";

interface VersionProps {
  versions: VersionT[];
}

export default function Version({ versions }: VersionProps) {
  return (
    <Card>
      <Card.Header as="h2" className="h6 font-weight-bold">
        Versions
      </Card.Header>
      <ListGroup variant="flush">
        {versions.map((version) => (
          <ListGroup.Item
            action
            active={version.current}
            className="d-flex justify-content-between align-items-center"
            disabled={version.current}
            href={encodeURI(version.url)}
            key={version.tag_or_hash}
            variant={version.current ? "light" : undefined}
          >
            {version.tag_or_hash}
            {version.status === "draft" ? (
              <Badge className="ml-1" variant="light">
                Draft
              </Badge>
            ) : null}
            {version.status === "under review" ? (
              <Badge className="ml-1" variant="info">
                Under review
              </Badge>
            ) : null}
            {version.status === "published" ? (
              <Badge className="ml-1" variant="success">
                Published
              </Badge>
            ) : null}
          </ListGroup.Item>
        ))}
      </ListGroup>
    </Card>
  );
}
