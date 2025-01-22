import "@testing-library/jest-dom";
import { render, screen } from "@testing-library/react";
import React from "react";
import { expect, it } from "vitest";
import Filter from "../../components/Filter";

it("Displays a filter", async () => {
  render(<Filter filter="Hello world" />);
  expect(
    screen.queryByText(
      "Filtered to Hello world concepts and their descendants.",
    ),
  ).toBeVisible;
});

it("Does not render if a filter is not provided", async () => {
  render(<Filter />);
  expect(screen.queryByText("Filtered to")).toBeNull;
});
