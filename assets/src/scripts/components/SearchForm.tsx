import React, { useState } from "react";
import { Button, Card, Form, InputGroup } from "react-bootstrap";
import { getCookie } from "../_utils";
import { PageData } from "../types";

interface SearchFormProps {
  codingSystemName: string;
  searchURL: PageData["searchURL"];
}

export default function SearchForm({
  codingSystemName,
  searchURL,
}: SearchFormProps) {
  // NB, if you change the max search length, remember to change it on
  // the server side as well in the models.py file
  const MAX_SEARCH_LENGTH = 255; // (codelists/models.py - Search - term)
  const MAX_CODE_LENGTH = 18; // (codelists/models.py - Search - code)

  type SearchOptionKeys = "term" | "code";
  const SEARCH_OPTIONS: {
    [K in SearchOptionKeys]: {
      label: string;
      value: K;
      placeholder: string;
      maxLength: number;
      validationMsg: string;
    };
  } = {
    term: {
      label: "Term",
      value: "term",
      placeholder: "Enter a search term...",
      maxLength: MAX_SEARCH_LENGTH,
      validationMsg: `Your search term has reached the maximum length of ${MAX_SEARCH_LENGTH} characters`,
    },
    code: {
      label: "Code",
      value: "code",
      placeholder: "Enter a clinical code...",
      maxLength: MAX_CODE_LENGTH,
      validationMsg: `Your clinical code has reached the maximum length of ${MAX_CODE_LENGTH} characters`,
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
      <Card.Header as="h6" className="p-2">
        Search the {codingSystemName} dictionary
      </Card.Header>
      <Form action={encodeURI(searchURL)} method="post" className="p-2">
        <Form.Control
          name="csrfmiddlewaretoken"
          type="hidden"
          value={getCookie("csrftoken")}
        />
        <Form.Group>
          <Form.Label>Search by:</Form.Label>
          <div>
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
          </div>
        </Form.Group>
        <Form.Group>
          <InputGroup className="mb-3">
            <Form.Control
              name="search"
              placeholder={SEARCH_OPTIONS[searchType].placeholder}
              type="search"
              value={searchTerm}
              onInput={handleSearchChange}
              maxLength={SEARCH_OPTIONS[searchType].maxLength}
              isInvalid={
                searchTerm.length >= SEARCH_OPTIONS[searchType].maxLength
              }
            />
            <InputGroup.Append>
              <Button name="field" type="submit" variant="primary">
                Search
              </Button>
            </InputGroup.Append>
            {searchTerm.length >= SEARCH_OPTIONS[searchType].maxLength && (
              <Form.Control.Feedback type="invalid">
                {SEARCH_OPTIONS[searchType].validationMsg}
              </Form.Control.Feedback>
            )}
          </InputGroup>
        </Form.Group>

        <Form.Group>
          <Form.Text className="text-muted">
            {codingSystemName === "ICD-10" &&
            searchType === SEARCH_OPTIONS.code.value ? (
              <p>
                You can use a wildcard search to find all ICD-10 codes starting
                with a certain string. E.g. use <code>xyz*</code> to find all
                codes starting with <code>xyz</code>. (Wildcard search only
                available for ICD-10.)
              </p>
            ) : null}
          </Form.Text>
        </Form.Group>
      </Form>
    </Card>
  );
}
