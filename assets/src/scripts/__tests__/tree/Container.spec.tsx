import "@testing-library/jest-dom";
import { render, screen } from "@testing-library/react";
import React from "react";
import { expect, it, vi } from "vitest";
import { readValueFromPage } from "../../_utils";
import Container from "../../tree/Container";

// Mock the readValueFromPage utility
vi.mock("../../_utils", () => ({
  readValueFromPage: vi.fn(),
}));

const mockTreeData = [
  {
    title: "Section One",
    children: [
      {
        id: "code-1",
        name: "Code One",
        status: "+" as const,
        children: [],
        depth: 0,
      },
    ],
  },
  {
    title: "Section Two",
    children: [
      {
        id: "code-2",
        name: "Code Two",
        status: "-" as const,
        children: [],
        depth: 0,
      },
    ],
  },
];

it("renders all sections from tree data", () => {
  // Mock the readValueFromPage to return our test data
  (readValueFromPage as ReturnType<typeof vi.fn>).mockReturnValue(mockTreeData);

  render(<Container />);

  // Check that both sections are rendered
  const sections = screen.getAllByRole("region");
  expect(sections).toHaveLength(2);

  // Check section titles
  const headings = screen.getAllByRole("heading", { level: 3 });
  expect(headings[0]).toHaveTextContent("Section One");
  expect(headings[1]).toHaveTextContent("Section Two");

  // Check that each section has a list
  const lists = screen.getAllByRole("list");
  expect(lists).toHaveLength(2);
});

it("handles empty tree data", () => {
  // Mock empty tree data
  (readValueFromPage as ReturnType<typeof vi.fn>).mockReturnValue([]);

  render(<Container />);

  // Should render without errors but with no sections
  const sections = screen.queryAllByRole("region");
  expect(sections).toHaveLength(0);
});
