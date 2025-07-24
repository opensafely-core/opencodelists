import React, { useState } from "react";
import { Button, Card, Form, ListGroup } from "react-bootstrap";
import { getCookie } from "../../_utils";
import type { PageData } from "../../types";

export interface SearchesProps {
  draftURL: PageData["draftURL"];
  isEditable: PageData["isEditable"];
  searches: {
    active: boolean;
    delete_url: string;
    term_or_code: string;
    url: string;
  }[];
}

export default function Searches({
  draftURL,
  isEditable,
  searches,
}: SearchesProps) {
  const [activeUrl, setActiveUrl] = useState<string>(
    () => searches.find((search) => search.active)?.url || "",
  );

  const handleClick = (url: string) => (e: React.MouseEvent) => {
    // Don't trigger if clicking the Remove button
    if (!(e.target as HTMLElement).closest("button")) {
      setActiveUrl(url);
    }
  };

  return (
    <Card>
      <Card.Header as="h2" className="h6 font-weight-bold">
        Previous searches
      </Card.Header>
      <ListGroup variant="flush">
        {searches.map((search) => (
          <React.Fragment key={search.url}>
            {search.delete_url && isEditable ? (
              <ListGroup.Item
                action
                active={search.url === activeUrl}
                href={search.url}
                onClick={handleClick(search.url)}
              >
                <Form
                  action={search.delete_url}
                  className="d-flex justify-content-between align-items-center"
                  method="post"
                >
                  <Form.Control
                    name="csrfmiddlewaretoken"
                    type="hidden"
                    value={getCookie("csrftoken")}
                  />
                  {search.term_or_code}
                  <Button
                    aria-label="remove search"
                    className="ml-2"
                    name="delete-search"
                    type="submit"
                    size="sm"
                    variant={
                      search.url === activeUrl ? "light" : "outline-danger"
                    }
                  >
                    Remove
                  </Button>
                </Form>
              </ListGroup.Item>
            ) : (
              <ListGroup.Item
                action
                active={search.active}
                href={encodeURI(search.url)}
              >
                {search.term_or_code}
              </ListGroup.Item>
            )}
          </React.Fragment>
        ))}

        {searches.some((search) => search.active) ? (
          <ListGroup.Item
            action
            className="font-italic"
            href={encodeURI(draftURL)}
            onClick={handleClick(draftURL)}
          >
            show all
          </ListGroup.Item>
        ) : null}
      </ListGroup>
    </Card>
  );
}
