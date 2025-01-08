import PropTypes from "prop-types";
import React from "react";
import { Button, Form, ListGroup } from "react-bootstrap";
import { getCookie } from "../_utils";

function Search({ search }) {
  return search.delete_url ? (
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
          variant="danger"
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
      key={search.url}
    >
      {search.term_or_code}
    </ListGroup.Item>
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
