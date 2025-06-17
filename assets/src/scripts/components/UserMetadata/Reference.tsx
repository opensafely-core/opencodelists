import React, { useState } from "react";
import { Button, Form, ListGroup } from "react-bootstrap";

export default function Reference({
  content,
  discard,
  inEditMode = false,
}: {
  content: {
    text: string;
    url: string;
  };
  discard?: Function;
  inEditMode?: boolean;
}) {
  const [isEditing, setIsEditing] = useState(inEditMode);
  const [textContent, setTextContent] = useState(content.text);
  const [urlContent, setUrlContent] = useState(content.url);

  function handleCancel() {
    if (discard) return discard();
    setTextContent(content.text);
    setUrlContent(content.url);
    setIsEditing(false);
  }

  return (
    <ListGroup.Item>
      {isEditing ? (
        <Form>
          <Form.Group className="mb-2">
            <Form.Label>Text</Form.Label>
            <Form.Control
              type="text"
              placeholder="Text to display"
              value={textContent}
              onChange={(event) => {
                setTextContent(event.target.value);
              }}
            />
          </Form.Group>
          <Form.Group className="mb-3">
            <Form.Label>URL</Form.Label>
            <Form.Control
              onChange={(event) => {
                setUrlContent(event.target.value);
              }}
              type="url"
              placeholder="URL to link to"
              value={urlContent}
            />
          </Form.Group>
          <div className="d-flex flex-row justify-content-end">
            <Button
              variant="success"
              size="sm"
              // onClick={handleSave}
            >
              Save
            </Button>
            <Button
              className="ml-1"
              onClick={handleCancel}
              size="sm"
              variant="secondary"
            >
              Cancel
            </Button>
          </div>
        </Form>
      ) : (
        <div className="d-flex align-items-center">
          <a href={content.url} target="_blank" rel="noopener noreferrer">
            {content.text}
          </a>
          <Button
            className="ml-auto"
            onClick={() => setIsEditing(true)}
            size="sm"
            variant="secondary"
          >
            Edit
          </Button>
          <Button
            className="ml-2"
            size="sm"
            variant="danger"
            // onClick={() => handleDelete(index)}
          >
            Delete
          </Button>
        </div>
      )}
    </ListGroup.Item>
  );
}
