import PropTypes from "prop-types";
import React from "react";
import { Button, Form } from "react-bootstrap";
import { getCookie } from "../_utils";

function Search({ search }) {
  return search.delete_url ? (
    <Form action={search.delete_url} className="mt-0 pt-0" method="post">
      <Form.Control
        name="csrfmiddlewaretoken"
        type="hidden"
        value={getCookie("csrftoken")}
      />

      <a
        className={
          search.active
            ? "list-group-item list-group-item-action active py-1 px-2"
            : "list-group-item list-group-item-action py-1 px-2 "
        }
        href={search.url}
      >
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
      </a>
    </Form>
  ) : (
    <a
      className={
        search.active
          ? "list-group-item list-group-item-action active py-1 px-2"
          : "list-group-item list-group-item-action py-1 px-2 "
      }
      href={encodeURI(search.url)}
    >
      {search.term_or_code}
    </a>
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
