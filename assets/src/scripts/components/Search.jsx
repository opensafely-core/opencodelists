import PropTypes from "prop-types";
import React from "react";
import { Button, Form, ListGroup } from "react-bootstrap";
import { getCookie } from "../_utils";

function Search({ draftURL, searches }) {
  return (
    <>
      <h3 className="h6">Searches</h3>
      <ListGroup>
        {searches.map((search) => (
          <React.Fragment key={search.url}>
            {search.delete_url ? (
              <ListGroup.Item
                action
                active={search.active}
                className="py-1 px-2"
                href={search.url}
              >
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
                    variant="secondary"
                  >
                    &times;
                  </Button>
                </Form>
              </ListGroup.Item>
            ) : (
              <ListGroup.Item
                action
                active={search.active}
                className="py-1 px-2"
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
            className="py-1 px-2 font-italic"
            href={encodeURI(draftURL)}
          >
            show all
          </ListGroup.Item>
        ) : null}
      </ListGroup>
      <hr />
    </>
  );
}

export default Search;

Search.propTypes = {
  search: PropTypes.shape({
    active: PropTypes.bool,
    delete_url: PropTypes.string,
    term_or_code: PropTypes.string,
    url: PropTypes.string,
  }),
};
