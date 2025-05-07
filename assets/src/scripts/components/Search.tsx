import React from "react";
import { Button, Card, Form, ListGroup } from "react-bootstrap";
import { getCookie } from "../_utils";
import { PageData } from "../types";

interface SearchProps {
  draftURL: PageData["draftURL"];
  searches: PageData["searches"];
}

export default function Search({ draftURL, searches }: SearchProps) {
  return (
    <Card>
      <Card.Header as="h2" className="h6 font-weight-bold">
        Previous searches
      </Card.Header>
      <ListGroup variant="flush">
        {searches.map((search) => (
          <React.Fragment key={search.url}>
            {search.delete_url ? (
              <ListGroup.Item action active={search.active} href={search.url}>
                <Form action={search.delete_url} method="post">
                  <Form.Control
                    name="csrfmiddlewaretoken"
                    type="hidden"
                    value={getCookie("csrftoken")}
                  />
                  {search.term_or_code}
                  <Button
                    aria-label="remove search"
                    className="float-right p-0 px-1"
                    name="delete-search"
                    type="submit"
                    size="sm"
                    variant={search.active ? "light" : "outline-primary"}
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
          >
            show all
          </ListGroup.Item>
        ) : null}
      </ListGroup>
    </Card>
  );
}
