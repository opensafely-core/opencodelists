import React, { useState } from "react";
import { getCookie, readValueFromPage } from "../../_utils";
import type { BUILDER_CONFIG, PageData } from "../../types";

export interface SearchesProps {
  isEditable: PageData["isEditable"];
  searches: {
    active: boolean;
    delete_url: string;
    term_or_code: string;
    url: string;
  }[];
}

export default function Searches({ isEditable, searches }: SearchesProps) {
  const { url }: BUILDER_CONFIG = readValueFromPage("builder-config");
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
      <h2 className="card-header h6 font-weight-bold">Previous searches</h2>
      <div className="list-group list-group-flush">
        {searches.map((search) => (
          <a
            className={`
                list-group-item list-group-item-action
                d-flex justify-content-between align-items-center
                ${search.url === activeUrl ? "active" : ""}
              `}
            href={search.url}
            key={search.url}
            onClick={handleClick(search.url)}
          >
            <div className="break-word">{search.term_or_code}</div>
            {search.delete_url && isEditable ? (
              <form action={search.delete_url} className="ml-2" method="post">
                <input
                  name="csrfmiddlewaretoken"
                  type="hidden"
                  className="form-control"
                  value={getCookie("csrftoken")}
                />
                <button
                  type="submit"
                  aria-label="remove search"
                  className={`
                    btn btn-sm
                    ${search.url === activeUrl ? "btn-light" : "btn-outline-danger"}
                  `}
                  name="delete-search"
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
            href={encodeURI(url.draft)}
            onClick={handleClick(url.draft)}
          >
            show all
          </a>
        ) : null}
      </div>
    </div>
  );
}
