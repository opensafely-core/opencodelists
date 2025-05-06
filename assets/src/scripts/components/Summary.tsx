import React from "react";
import { Card, ListGroup } from "react-bootstrap";
import { PageData } from "../types";

interface SummaryProps {
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

  return (
    <Card>
      <Card.Header as="h6" className="p-2">
        Concepts found ({counts.total})
      </Card.Header>
      <ListGroup variant="flush">
        {counts["+"] > 0 && (
          <ListGroup.Item
            action
            href={encodeURI(draftURL + "?filter=included")}
            active={currentFilter === "included"}
            className="p-2 pl-3"
            as="a"
          >
            <span id="summary-included">{counts["+"] + counts["(+)"]}</span>{" "}
            included concepts
          </ListGroup.Item>
        )}
        {counts["-"] > 0 && (
          <ListGroup.Item
            action
            href={encodeURI(draftURL + "?filter=excluded")}
            active={currentFilter === "excluded"}
            className="p-2 pl-3"
          >
            <span id="summary-excluded">{counts["-"] + counts["(-)"]}</span>{" "}
            excluded concepts
          </ListGroup.Item>
        )}
        {counts["?"] > 0 && (
          <ListGroup.Item
            action
            href={encodeURI(draftURL + "?filter=unresolved")}
            active={currentFilter === "unresolved"}
            className="p-2 pl-3"
          >
            <span id="summary-unresolved">{counts["?"]}</span> unresolved
            concepts
          </ListGroup.Item>
        )}
        {counts["!"] > 0 && (
          <ListGroup.Item
            action
            href={encodeURI(draftURL + "?filter=in-conflict")}
            active={currentFilter === "in-conflict"}
            className="p-2 pl-3"
          >
            <span id="summary-in-conflict">{counts["!"]}</span> conflicted
            concepts
          </ListGroup.Item>
        )}
        {currentFilter ? (
          <ListGroup.Item
            action
            className="py-1 px-2 font-italic"
            href={encodeURI(draftURL)}
          >
            show all {counts.total} matching concepts
          </ListGroup.Item>
        ) : null}
      </ListGroup>
    </Card>
  );
}
