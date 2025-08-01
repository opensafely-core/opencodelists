import React, { useState } from "react";
import { getCookie, readValueFromPage } from "../../_utils";
import type { DRAFT_URL, IS_EDITABLE, SEARCHES } from "../../types";

export default function Searches() {
  const draftURL: DRAFT_URL = readValueFromPage("draft-url");
  const isEditable: IS_EDITABLE = readValueFromPage("is-editable");
  const searches: SEARCHES = readValueFromPage("searches");

  const [activeUrl, setActiveUrl] = useState<string>(
    () => searches?.find((search) => search.active)?.url || "",
  );

  const handleClick = (url: string) => (e: React.MouseEvent) => {
    // Don't trigger if clicking the Remove button
    if (!(e.target as HTMLElement).closest("button")) {
      setActiveUrl(url);
    }
  };

  if (!searches?.length) return null;

  return (
    <div className="card">
      <h2 className="card-header h6 font-weight-bold">Previous searches</h2>
      <div className="list-group list-group-flush">
        {searches.map((search) => (
          <a
            aria-label={search.term_or_code}
            className={`
              list-group-item list-group-item-action
              d-flex justify-content-between align-items-center flex-wrap break-word
              ${search.url === activeUrl ? "active" : ""}
            `}
            href={search.url}
            key={search.url}
            onClick={handleClick(search.url)}
          >
            {search.term_or_code}
            {search.delete_url && isEditable ? (
              <form action={search.delete_url} className="" method="POST">
                <input
                  className="form-control"
                  name="csrfmiddlewaretoken"
                  type="hidden"
                  value={getCookie("csrftoken")}
                />
                <button
                  aria-label="remove search"
                  className={`btn btn-sm btn-${search.url === activeUrl ? "light" : "outline-danger"}`}
                  name="delete-search"
                  type="submit"
                >
                  Remove
                </button>
              </form>
            ) : null}
          </a>
        ))}

        {searches.some((search) => search.active) ? (
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
