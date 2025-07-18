import React, { useState } from "react";
import { Button, Form, ListGroup } from "react-bootstrap";
import { getCookie, readValueFromPage } from "../../_utils";
import { DRAFT_URL, IS_EDITABLE, SEARCHES } from "../../types";

export default function Searches() {
  const draftURL: DRAFT_URL = readValueFromPage("draft-url");
  const isEditable: IS_EDITABLE = readValueFromPage("is-editable");
  const searches: SEARCHES = readValueFromPage("searches");

  if (!searches?.length) return null;

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
    <div className="card">
      <h2 className="h6 font-weight-bold card-header">Previous searches</h2>
      <div className="list-group list-group-flush">
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

        {draftURL && searches.some((search) => search.active) ? (
          <a
            className="list-group-item list-group-item-action font-italic"
            href={encodeURI(draftURL)}
            onClick={handleClick(draftURL)}
          >
            show all
          </a>
        ) : null}
      </div>
    </div>
  );
}
