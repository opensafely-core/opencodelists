import React, { useState } from "react";
import { Card, ListGroup } from "react-bootstrap";
import Reference from "./Reference";

export default function References({
  references,
}: {
  references: {
    text: string;
    url: string;
  }[];
}) {
  const [isAdding, setIsAdding] = useState(false);
  // async function handleDelete() {}
  // async function handleSave() {}

  const [keyRefs, _] = useState(
    references?.map((ref) => ({ id: crypto.randomUUID(), ...ref })),
  );

  return (
    <Card as="form">
      <Card.Header>
        <Card.Title className="mb-1">
          <h3 className="h5 mb-0">References</h3>
        </Card.Title>
        <Card.Text className="small">
          Sometimes it's useful to provide links, for example links to
          algorithms, methodologies or papers that are relevant to this codelist
        </Card.Text>
      </Card.Header>
      {keyRefs ? (
        <ListGroup variant="flush" as="ul">
          {keyRefs.map((reference) => (
            <Reference content={reference} key={reference.id} />
          ))}
        </ListGroup>
      ) : null}

      <Card.Footer>
        {isAdding ? (
          <Reference
            content={{ text: "", url: "" }}
            discard={() => setIsAdding(false)}
            inEditMode={true}
          />
        ) : (
          <button
            onClick={() => setIsAdding(true)}
            type="button"
            className="btn btn-primary btn-sm"
          >
            {keyRefs.length === 0 ? "Add a reference" : "Add another reference"}
          </button>
        )}
      </Card.Footer>
    </Card>
  );
}
