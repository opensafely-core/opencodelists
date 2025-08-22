/** biome-ignore-all lint/correctness/useUniqueElementIds: IDs required by Django */
import React, { useState } from "react";
import { getCookie, readValueFromPage } from "../../_utils";

export default function SearchForm() {
  const codingSystemName = readValueFromPage("metadata")?.coding_system_name;
  const searchURL = readValueFromPage("search-url");

  // NB, if you change the max search length, remember to change it on
  // the server side as well in the models.py file
  const MIN_TERM_LENGTH = 3; // (codelists/models.py - Search - term, MinLengthValidator)
  const MAX_TERM_LENGTH = 255; // (codelists/models.py - Search - term, max_length)
  const MIN_CODE_LENGTH = 1; // (codelists/models.py - Search - code, MinLengthValidator)
  const MAX_CODE_LENGTH = 18; // (codelists/models.py - Search - code, max_length)

  type SearchOptionKeys = "term" | "code";
  const SEARCH_OPTIONS: {
    [K in SearchOptionKeys]: {
      label: string;
      value: K;
      placeholder: string;
      minLength: number;
      maxLength: number;
      validationMaxLengthMsg: string;
    };
  } = {
    term: {
      label: "Term",
      value: "term",
      placeholder: "Enter a search term…",
      minLength: MIN_TERM_LENGTH,
      maxLength: MAX_TERM_LENGTH,
      validationMaxLengthMsg: `Your search term has reached the maximum length of ${MAX_TERM_LENGTH} characters`,
    },
    code: {
      label: "Code",
      value: "code",
      placeholder: "Enter a clinical code…",
      minLength: MIN_CODE_LENGTH,
      maxLength: MAX_CODE_LENGTH,
      validationMaxLengthMsg: `Your clinical code has reached the maximum length of ${MAX_CODE_LENGTH} characters`,
    },
  };
  const [searchTerm, setSearchTerm] = useState("");
  const [searchType, setSearchType] = useState<SearchOptionKeys>(
    SEARCH_OPTIONS.term.value,
  );

  if (!codingSystemName || !searchURL) return null;

  const handleSearchChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const value = e.target.value;
    if (value.length <= SEARCH_OPTIONS[searchType].maxLength) {
      setSearchTerm(value);
    }
  };

  const handleSearchTypeChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    setSearchType(e.target.value as SearchOptionKeys);
  };

  return (
    <div className="card">
      <h2 className="card-header h6 font-weight-bold">
        Search the {codingSystemName} dictionary
      </h2>
      <div className="card-body pt-2 pb-1">
        <form action={encodeURI(searchURL)} method="POST">
          <input
            className="form-control"
            name="csrfmiddlewaretoken"
            type="hidden"
            value={getCookie("csrftoken")}
          />
          <fieldset>
            <div className="form-group">
              <legend className="form-label h6 mt-1">Search by:</legend>
              {Object.values(SEARCH_OPTIONS).map((option) => (
                <div
                  className="form-check form-check-inline"
                  key={option.value}
                >
                  <input
                    checked={searchType === option.value}
                    className="form-check-input"
                    id={`search-type-${option.value}`}
                    name="search-type"
                    onChange={handleSearchTypeChange}
                    type="radio"
                    value={option.value}
                  />
                  <label
                    className="form-check-label"
                    htmlFor={`search-type-${option.value}`}
                  >
                    {option.label}
                  </label>
                </div>
              ))}
            </div>
          </fieldset>
          <div className="form-group">
            <div className="input-group">
              <label className="form-label sr-only" htmlFor="searchInput">
                {SEARCH_OPTIONS[searchType].placeholder}
              </label>
              <input
                className={`form-control ${searchTerm.length >= SEARCH_OPTIONS[searchType].maxLength ? "is-invalid" : ""}`}
                id="searchInput"
                minLength={SEARCH_OPTIONS[searchType].minLength}
                maxLength={SEARCH_OPTIONS[searchType].maxLength}
                name="search"
                onInput={handleSearchChange}
                placeholder={SEARCH_OPTIONS[searchType].placeholder}
                required={true}
                type="search"
                value={searchTerm}
              />
              <div className="input-group-append">
                <button className="btn btn-primary" name="field" type="submit">
                  Search
                </button>
              </div>
              {searchTerm.length >= SEARCH_OPTIONS[searchType].maxLength && (
                <div className="invalid-feedback">
                  {SEARCH_OPTIONS[searchType].validationMaxLengthMsg}
                </div>
              )}
            </div>
          </div>

          {codingSystemName === "ICD-10" &&
          searchType === SEARCH_OPTIONS.code.value ? (
            <small className="form-text text-muted">
              <p>
                You can use a wildcard search to find all ICD-10 codes starting
                with a certain string. E.g. use <code>xyz*</code> to find all
                codes starting with <code>xyz</code>. (Wildcard search only
                available for ICD-10.)
              </p>
            </small>
          ) : null}
        </form>
      </div>
    </div>
  );
}
