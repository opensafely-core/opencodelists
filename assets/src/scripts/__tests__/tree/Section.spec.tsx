import "@testing-library/jest-dom";
import { render, screen } from "@testing-library/react";
import React from "react";
import { expect, it } from "vitest";
import Section from "../../tree/Section";

const mockSection = {
  children: [
    {
      id: "test-code-1",
      name: "Test Code 1",
      status: "+" as const,
      children: [],
      depth: 0,
    },
    {
      id: "test-code-2",
      name: "Test Code 2",
      status: "-" as const,
      children: [],
      depth: 0,
    },
  ],
  title: "Test Section",
};

it("renders the section with correct title and attributes", () => {
  render(
    <Section section={mockSection} slug="test-section" title="Test Section" />,
  );

  const section = screen.getByRole("region");
  expect(section).toBeVisible();

  const heading = screen.getByRole("heading", { level: 3 });
  expect(heading).toHaveTextContent("Test Section");

  const list = screen.getByRole("list");
  expect(list).toHaveAttribute(
    "title",
    "Codes within the Test Section section",
  );
});

it("renders ListGroup with correct data", () => {
  render(
    <Section section={mockSection} slug="test-section" title="Test Section" />,
  );

  const list = screen.getByRole("list");
  expect(list).toBeVisible();
  expect(list.children).toHaveLength(mockSection.children.length);
});
