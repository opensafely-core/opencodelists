import React from "react";
import { getCookie } from "../_utils";

function SearchForm({ codingSystemName, searchURL }) {
  return (
    <form action={searchURL} method="post">
      <div className="form-group">
        <input
          name="csrfmiddlewaretoken"
          type="hidden"
          value={getCookie("csrftoken")}
        />
        <input
          className="form-control"
          name="search"
          placeholder="Term or code"
          type="search"
        />
      </div>
      <div>
        <button
          className="btn btn-sm btn-primary mr-1"
          name="field"
          type="submit"
        >
          Search
        </button>
      </div>
      <div>
        <small className="form-text text-muted">
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
        </small>
      </div>
    </form>
  );
}

export default SearchForm;
