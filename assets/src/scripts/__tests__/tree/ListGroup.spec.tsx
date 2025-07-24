import "@testing-library/jest-dom";
import { render, screen } from "@testing-library/react";
import React from "react";
import { describe, expect, it } from "vitest";
import ListGroup, { type CodeProps } from "../../tree/ListGroup";

const mockCode: CodeProps = {
  id: "test-code",
  name: "Test Code",
  status: "+",
  children: [],
  depth: 0,
};

const mockCodeWithChildren: CodeProps = {
  id: "parent-code",
  name: "Parent Code",
  status: "+",
  children: [
    {
      id: "child-code-1",
      name: "Child Code 1",
      status: "+",
      children: [],
      depth: 1,
    },
    {
      id: "child-code-2",
      name: "Child Code 2",
      status: "-",
      children: [],
      depth: 1,
    },
  ],
  depth: 0,
};

describe("ListGroup Component", () => {
  it("renders a single code item without children", () => {
    render(<ListGroup data={[mockCode]} />);

    const item = screen.getByTitle("Test Code");
    expect(item).toBeVisible();
    expect(screen.getByText("Included")).toBeVisible();
    expect(screen.getByText("Test Code")).toBeVisible();
    expect(screen.getByText("test-code")).toBeVisible();
  });

  it("renders a code item with excluded status", () => {
    const excludedCode = { ...mockCode, status: "-" as const };
    render(<ListGroup data={[excludedCode]} />);

    const item = screen.getByTitle("Test Code");
    expect(item).toBeVisible();
    expect(screen.getByText("Excluded")).toBeVisible();
    expect(screen.getByText("Test Code")).toBeVisible();
    expect(screen.getByText("test-code")).toBeVisible();
  });

  it("renders a code item with children in a dropdown", () => {
    render(<ListGroup data={[mockCodeWithChildren]} />);

    // Check that the parent item is rendered
    const parentItem = screen.getByTitle("Parent Code");
    expect(parentItem).toBeVisible();

    // Check that the dropdown is rendered
    const details = parentItem.querySelector("details");
    expect(details).toBeVisible();
    expect(details).toHaveAttribute("open"); // Should be open by default for depth < 2

    // Check that children are rendered
    expect(screen.getByText("Child Code 1")).toBeVisible();
    expect(screen.getByText("Child Code 2")).toBeVisible();
  });

  it("renders multiple code items", () => {
    const multipleCodes = [
      mockCode,
      { ...mockCode, id: "test-code-2", name: "Test Code 2" },
    ];

    render(<ListGroup data={multipleCodes} />);

    expect(screen.getByTitle("Test Code")).toBeVisible();
    expect(screen.getByTitle("Test Code 2")).toBeVisible();
  });

  it("renders nested children correctly, hiding items with depth > 2", () => {
    const nestedCode: CodeProps = {
      id: "grandparent",
      name: "Grandparent",
      status: "+",
      children: [
        {
          id: "parent",
          name: "Parent",
          status: "+",
          children: [
            {
              id: "child",
              name: "Child",
              status: "+",
              children: [
                {
                  id: "hidden-code",
                  name: "Hidden Code",
                  status: "+",
                  children: [],
                  depth: 3,
                },
              ],
              depth: 2,
            },
          ],
          depth: 1,
        },
      ],
      depth: 0,
    };

    render(<ListGroup data={[nestedCode]} />);

    expect(screen.getByTitle("Grandparent")).toBeVisible();
    expect(screen.getByTitle("Parent")).toBeVisible();
    expect(screen.getByTitle("Child")).toBeVisible();
    expect(screen.getByTitle("Hidden Code")).not.toBeVisible();
  });

  it("handles empty data array", () => {
    render(<ListGroup data={[]} />);
    expect(document.querySelector(".tree__list")).toBeNull();
  });
});
