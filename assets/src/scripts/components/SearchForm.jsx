import PropTypes from "prop-types";
import React from "react";
import { Button, Form } from "react-bootstrap";
import { getCookie } from "../_utils";

function SearchForm({ codingSystemName, searchURL }) {
  return (
    <Form action={encodeURI(searchURL)} method="post">
      <Form.Group>
        <Form.Control
          name="csrfmiddlewaretoken"
          type="hidden"
          value={getCookie("csrftoken")}
        />
        <Form.Control name="search" placeholder="Term or code" type="search" />
      </Form.Group>
      <Form.Group>
        <Button
          className="mr-1"
          name="field"
          size="sm"
          type="submit"
          variant="primary"
        >
          Search
        </Button>
      </Form.Group>
      <Form.Group>
        <Form.Text className="text-muted">
          {codingSystemName === "ICD-10" ? (
            <p>
              To search by code, prefix your search with <code>code:</code>. For
              instance, use <code>code:xyz</code> to find the concept with code{" "}
              <code>xyz</code>, or <code>code:xyz*</code> to find all concepts
              with codes beginning <code>xyz</code>. (Wildcard search only
              available for ICD-10.)
            </p>
          ) : (
            <p>
              To search by code, prefix your search with <code>code:</code>. For
              instance, use <code>code:xyz</code> to find the concept with code{" "}
              <code>xyz</code>.
            </p>
          )}
          <p>
            Otherwise, searching will return all concepts with a description
            containing the search term.
          </p>
          <p>
            We plan to support boolean search operators (eg{" "}
            <code>ambulatory AND blood pressure</code>) in future.
          </p>
        </Form.Text>
      </Form.Group>
    </Form>
  );
}

export default SearchForm;

SearchForm.propTypes = {
  codingSystemName: PropTypes.string,
  searchURL: PropTypes.string,
};
