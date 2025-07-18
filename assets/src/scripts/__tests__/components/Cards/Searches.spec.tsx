import "@testing-library/jest-dom";
import { render, screen } from "@testing-library/react";
import React from "react";
import { describe, expect, it } from "vitest";
import Search, { SearchesProps } from "../../../components/Cards/Searches";

describe("Search Component", () => {
  const mockSearches: SearchesProps["searches"] = [
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

  const baseProps = {
    draftURL: "/draft/",
    searches: mockSearches,
  };

  it("renders the search card with header", () => {
    render(<Search {...baseProps} isEditable={true} />);
    expect(
      screen.getByRole("heading", { name: "Previous searches" }),
    ).toBeVisible();
  });

  it("renders remove link only when isEditable is true and delete_url exists", () => {
    render(<Search {...baseProps} isEditable={true} />);
    const removeLinks = screen.getAllByRole("link", { name: /Remove/ });
    expect(removeLinks.length).toBe(1); // Only one item has delete_url.
    expect(removeLinks[0]).toBeVisible();
  });

  it("does not render remove link when isEditable is false", () => {
    render(<Search {...baseProps} isEditable={false} />);
    expect(screen.queryByRole("link", { name: /Remove/ })).toBeNull();
  });

  it("renders the correct number of search items", () => {
    render(<Search {...baseProps} isEditable={true} />);
    const items = screen.getAllByRole("link");
    expect(items.length).toBe(mockSearches.length + 1); // +1 for the "show all" item.
  });

  it("renders 'show all' link when there's an active search", () => {
    render(<Search {...baseProps} isEditable={true} />);
    expect(screen.queryByRole("link", { name: "show all" })).toBeVisible();
  });

  it("does not render 'show all' link when no active search", () => {
    const mockSearchesNoActiveSearch: SearchesProps["searches"] = [
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
    ];

    render(
      <Search
        {...baseProps}
        searches={mockSearchesNoActiveSearch}
        isEditable={true}
      />,
    );
    expect(screen.queryByRole("link", { name: "show all" })).toBeNull();
  });
});
