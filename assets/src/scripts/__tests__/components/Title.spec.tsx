import "@testing-library/jest-dom";
import { render, screen } from "@testing-library/react";
import React from "react";
import { expect, it } from "vitest";
import Title from "../../components/Title";

it("renders the title with the provided name", () => {
  render(<Title name="Test Title" />);
  expect(screen.getByText("Test Title")).toBeInTheDocument();
});

it("renders the Draft badge", () => {
  render(<Title name="Test Title" />);
  expect(screen.getByText("Draft")).toBeInTheDocument();
});

it("renders the Badge with secondary variant", () => {
  render(<Title name="Test Title" />);
  const badge = screen.getByText("Draft");
  expect(badge).toHaveClass("badge-secondary");
});
