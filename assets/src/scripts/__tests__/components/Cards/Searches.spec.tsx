import "@testing-library/jest-dom";
import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import React from "react";
import { afterEach, beforeEach, describe, expect, it } from "vitest";
import Search from "../../../components/Cards/Searches";
import type { SEARCHES } from "../../../types";
import { cleanupScriptTags, scriptTagSetup } from "../../utils";

const mockSearches: SEARCHES = [
  {
    active: true,
    term_or_code: "test search 1",
    url: "/search/1/",
    delete_url: "/delete/1/",
  },
  {
    active: false,
    term_or_code: "test search 2",
    url: "/search/2/",
    delete_url: "",
  },
];

const draftURL = "/draft/";

describe("Search Component", () => {
  beforeEach(() =>
    scriptTagSetup({
      draftURL: draftURL,
      isEditable: true,
      searches: mockSearches,
    }),
  );
  afterEach(() => cleanupScriptTags(["draft-url", "is-editable", "searches"]));

  it("renders the search card with header", () => {
    render(<Search />);
    expect(
      screen.getByRole("heading", { name: "Previous searches" }),
    ).toBeVisible();
  });

  it("renders remove link only when isEditable is true", () => {
    render(<Search />);
    const removeLinks = screen.getAllByRole("button", {
      name: "remove search",
    });
    expect(removeLinks.length).toBe(1); // Only one item has delete_url.
    expect(removeLinks[0]).toBeVisible();
  });

  it("does not render remove link when isEditable is false", () => {
    cleanupScriptTags(["draft-url", "is-editable", "searches"]);
    scriptTagSetup({
      draftURL: draftURL,
      isEditable: false,
      searches: mockSearches,
    });
    render(<Search />);
    expect(screen.queryByRole("link", { name: /Remove/ })).toBeNull();
  });

  it("sets activeUrl on item click, but not when clicking the Remove button", async () => {
    const user = userEvent.setup();
    render(<Search />);

    expect(screen.getByRole("link", { name: "test search 2" })).not.toHaveClass(
      "active",
    );
    await user.click(screen.getByRole("link", { name: "test search 2" }));
    expect(screen.getByRole("link", { name: "test search 2" })).toHaveClass(
      "active",
    );

    const removeButton = screen.getByRole("button", { name: "remove search" });
    await user.click(removeButton);

    expect(screen.getByRole("link", { name: "test search 1" })).not.toHaveClass(
      "active",
    );
  });

  it("renders the correct number of search items", () => {
    render(<Search />);
    const items = screen.getAllByRole("link");
    expect(items.length).toBe(mockSearches.length + 1); // +1 for the "show all" item.
  });

  it("renders 'show all' link when there's an active search", () => {
    render(<Search />);
    expect(screen.queryByRole("link", { name: "show all" })).toBeVisible();
  });

  it("does not render 'show all' link when no active search", () => {
    cleanupScriptTags(["draft-url", "is-editable", "searches"]);
    scriptTagSetup({
      draftURL: draftURL,
      isEditable: true,
      searches: [
        {
          active: false,
          term_or_code: "test search 1",
          url: "/search/1/",
          delete_url: "/delete/1/",
        },
        {
          active: false,
          term_or_code: "test search 2",
          url: "/search/2/",
          delete_url: "",
        },
      ],
    });
    render(<Search />);
    expect(screen.queryByRole("link", { name: "show all" })).toBeNull();
  });
});
