import "@testing-library/jest-dom";
import { render, screen } from "@testing-library/react";
import { userEvent } from "@testing-library/user-event";
import React from "react";
import { expect, it, vi } from "vitest";
import DescendantToggle from "../../../components/Codelist/DescendantToggle";

it("Show a minus symbol if expanded", async () => {
  render(
    <DescendantToggle isExpanded path="/" toggleVisibility={() => null} />,
  );
  expect(screen.queryByText("⊟")).toBeVisible;
  expect(screen.queryByText("⊞")).toBeNull;
});

it("Show a plus symbol if not expanded", async () => {
  render(
    <DescendantToggle
      isExpanded={false}
      path="/"
      toggleVisibility={() => null}
    />,
  );
  expect(screen.queryByText("⊞")).toBeVisible;
  expect(screen.queryByText("⊟")).toBeNull;
});

it("Triggers the toggle visibility function", async () => {
  const fn = vi.fn();

  render(
    <DescendantToggle isExpanded path="/test-path/" toggleVisibility={fn} />,
  );

  await userEvent.click(screen.getByText("⊟"));

  expect(fn.mock.calls[0][0]).toBe("/test-path/");
});
