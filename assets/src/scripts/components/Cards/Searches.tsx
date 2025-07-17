import React, { useState } from "react";
import { getCookie } from "../../_utils";
import { useSidebarContext } from "../../context/sidebar-context";

export default function Searches() {
  const { draftURL, isEditable, searches } = useSidebarContext();
  const [activeUrl, setActiveUrl] = useState<string>(
    () => searches.find((search) => search.active)?.url || "",
  );

  const handleClick = (url: string) => (e: React.MouseEvent) => {
    // Don't trigger if clicking the Remove button
    if (!(e.target as HTMLElement).closest("button")) {
      setActiveUrl(url);
    }
  };

  if (!searches.length) return null;

  return (
    <div className="card">
      <h2 className="h6 font-weight-bold card-header">Previous searches</h2>
      <div className="list-group list-group-flush">
        {searches.map((search) => (
          <React.Fragment key={search.url}>
            {search.delete_url && isEditable ? (
              <a
                className={`list-group-item list-group-item-action ${search.active ? "active" : ""}`}
                href={search.url}
                onClick={handleClick(search.url)}
              >
                <form
                  action={search.delete_url}
                  className="d-flex justify-content-between align-items-center"
                  method="post"
                >
                  <input
                    name="csrfmiddlewaretoken"
                    type="hidden"
                    className="form-control"
                    value={getCookie("csrftoken")}
                  />
                  {search.term_or_code}
                  <button
                    aria-label="remove search"
                    className={`btn btn-sm ml-2 ${search.url === activeUrl ? "btn-light" : "btn-outline-danger"}`}
                    name="delete-search"
                    type="submit"
                  >
                    Remove
                  </button>
                </form>
              </a>
            ) : (
              <a
                href={encodeURI(search.url)}
                className={`list-group-item list-group-item-action ${search.active ? "active" : ""}`}
              >
                {search.term_or_code}
              </a>
            )}
          </React.Fragment>
        ))}

        {searches.some((search) => search.active) ? (
          <a
            className="font-italic list-group-item list-group-item-action"
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
