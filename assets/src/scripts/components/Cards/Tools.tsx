import React, { useState } from "react";
import { Card, ListGroup } from "react-bootstrap";
import { readValueFromPage } from "../../_utils";
import listOfTools from "../../data/tools.json";

export default function Tools() {
  const codingSystemId: string =
    readValueFromPage("metadata")?.coding_system_id;

  const [tools] = useState(() => {
    return listOfTools.filter((tool) =>
      tool.codingSystem.includes(codingSystemId),
    );
  });

  if (!codingSystemId || !tools.length) return null;

  return (
    <Card>
      <Card.Header>
        <h2 className="h6 font-weight-bold mb-1">Tools</h2>
        <p className="small mb-0">
          Tools to help you to build a better and more accurate codelist.
        </p>
      </Card.Header>
      <ListGroup as="ul" variant="flush">
        {tools.map((tool) => (
          <ListGroup.Item key={tool.id} as="li">
            <a
              href={tool.link}
              target="_blank"
              rel="noopener noreferrer"
              className={`plausible-event-name=Builder+tool+click plausible-event-tool=${tool.id}`}
            >
              {tool.name}
            </a>
            {tool?.description && (
              <p className="small mb-0">{tool.description}</p>
            )}
          </ListGroup.Item>
        ))}
      </ListGroup>
    </Card>
  );
}
