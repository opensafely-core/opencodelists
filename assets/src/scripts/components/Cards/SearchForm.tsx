import React, { useState } from "react";
import { Button, Card, Form, InputGroup } from "react-bootstrap";
import { getCookie } from "../../_utils";
import { useSidebarContext } from "../../context/sidebar-context";

export default function SearchForm() {
  const {
    isEditable,
    metadata: { coding_system_name: codingSystemName },
    searchURL,
  } = useSidebarContext();

  if (!isEditable || !codingSystemName || !searchURL) return null;

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
    <Card>
      <Card.Header as="h2" className="h6 font-weight-bold">
        Search the {codingSystemName} dictionary
      </Card.Header>
      <Card.Body className="pt-2 pb-1">
        <Form action={encodeURI(searchURL)} method="post">
          <Form.Control
            name="csrfmiddlewaretoken"
            type="hidden"
            value={getCookie("csrftoken")}
          />
          <fieldset>
            <Form.Group>
              <Form.Label className="h6 mt-1" as="legend">
                Search by:
              </Form.Label>
              {Object.values(SEARCH_OPTIONS).map((option) => (
                <Form.Check
                  key={option.value}
                  inline
                  label={option.label}
                  name="search-type"
                  type="radio"
                  id={`search-type-${option.value}`}
                  value={option.value}
                  checked={searchType === option.value}
                  onChange={handleSearchTypeChange}
                />
              ))}
            </Form.Group>
          </fieldset>
          <Form.Group>
            <InputGroup>
              <Form.Label srOnly htmlFor="searchInput">
                {SEARCH_OPTIONS[searchType].placeholder}
              </Form.Label>
              <Form.Control
                id="searchInput"
                name="search"
                placeholder={SEARCH_OPTIONS[searchType].placeholder}
                type="search"
                value={searchTerm}
                onInput={handleSearchChange}
                minLength={SEARCH_OPTIONS[searchType].minLength}
                maxLength={SEARCH_OPTIONS[searchType].maxLength}
                isInvalid={
                  searchTerm.length >= SEARCH_OPTIONS[searchType].maxLength
                }
                required
              />
              <InputGroup.Append>
                <Button name="field" type="submit" variant="primary">
                  Search
                </Button>
              </InputGroup.Append>
              {searchTerm.length >= SEARCH_OPTIONS[searchType].maxLength && (
                <Form.Control.Feedback type="invalid">
                  {SEARCH_OPTIONS[searchType].validationMaxLengthMsg}
                </Form.Control.Feedback>
              )}
            </InputGroup>
          </Form.Group>

          <Form.Group>
            <Form.Text className="text-muted">
              {codingSystemName === "ICD-10" &&
              searchType === SEARCH_OPTIONS.code.value ? (
                <p>
                  You can use a wildcard search to find all ICD-10 codes
                  starting with a certain string. E.g. use <code>xyz*</code> to
                  find all codes starting with <code>xyz</code>. (Wildcard
                  search only available for ICD-10.)
                </p>
              ) : null}
            </Form.Text>
          </Form.Group>
        </Form>
      </Card.Body>
    </Card>
  );
}
