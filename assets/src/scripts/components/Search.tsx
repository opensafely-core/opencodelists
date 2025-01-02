import React from "react";
import { getCookie } from "../_utils";

export interface SearchProps {
  search: {
    active: boolean;
    delete_url: string;
    term_or_code: string;
    url: string;
  };
}

function Search({ search }: SearchProps) {
  return search.delete_url ? (
    <form action={search.delete_url} className="mt-0 pt-0" method="post">
      <input
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

        <button
          className="btn badge badge-secondary float-right"
          name="delete-search"
          type="submit"
        >
          x
        </button>
      </a>
    </form>
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
