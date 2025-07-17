import React from "react";
import { Card, ListGroup } from "react-bootstrap";
import { useSidebarContext } from "../../context/sidebar-context";

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
  const { draftURL } = useSidebarContext();
  const currentFilter = new URLSearchParams(window.location.search).get(
    "filter",
  );

  const itemHref = (filter: string) =>
    encodeURI(`${draftURL}?filter=${filter}`);

  return (
    <Card>
      <Card.Header as="h2" className="h6 font-weight-bold">
        Concepts found ({counts.total})
      </Card.Header>
      <ListGroup variant="flush">
        {counts["+"] > 0 && (
          <ListGroup.Item
            action
            active={currentFilter === "included"}
            href={itemHref("included")}
            id="summary-included"
          >
            {counts["+"] + counts["(+)"]} included concepts
          </ListGroup.Item>
        )}
        {counts["-"] > 0 && (
          <ListGroup.Item
            action
            active={currentFilter === "excluded"}
            href={itemHref("excluded")}
            id="summary-excluded"
          >
            {counts["-"] + counts["(-)"]} excluded concepts
          </ListGroup.Item>
        )}
        {counts["?"] > 0 && (
          <ListGroup.Item
            action
            active={currentFilter === "unresolved"}
            href={itemHref("unresolved")}
            id="summary-unresolved"
          >
            {counts["?"]} unresolved concepts
          </ListGroup.Item>
        )}
        {counts["!"] > 0 && (
          <ListGroup.Item
            action
            active={currentFilter === "in-conflict"}
            href={itemHref("in-conflict")}
            id="summary-in-conflict"
          >
            {counts["!"]} conflicted concepts
          </ListGroup.Item>
        )}
        {currentFilter ? (
          <ListGroup.Item
            action
            className="font-italic"
            href={encodeURI(draftURL)}
          >
            show all {counts.total} matching concepts
          </ListGroup.Item>
        ) : null}
      </ListGroup>
    </Card>
  );
}
