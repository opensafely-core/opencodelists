import "@testing-library/jest-dom";
import { render, screen } from "@testing-library/react";
import { userEvent } from "@testing-library/user-event";
import React from "react";
import { describe, expect, it, vi } from "vitest";
import ManagementForm from "../../../components/Header/ManagementForm";

// Mock the getCookie utility
vi.mock("../../../_utils", () => ({
  getCookie: vi.fn(() => "test-csrf-token"),
}));

describe("ManagementForm", () => {
  const defaultCounts = {
    "!": 0,
    "(+)": 0,
    "(-)": 0,
    "+": 0,
    "-": 0,
    "?": 0,
    total: 0,
  };

  it("renders all form buttons", () => {
    render(<ManagementForm counts={defaultCounts} />);

    expect(screen.getByText("Save for review")).toBeVisible();
    expect(screen.getByText("Save draft")).toBeVisible();
    expect(screen.getByText("Discard")).toBeVisible();
  });

  it("disables 'Save for review' button when there are no items added", () => {
    render(<ManagementForm counts={defaultCounts} />);

    const saveForReviewButton = screen.getByRole("button", {
      name: "Save for review",
    });
    expect(saveForReviewButton).toBeDisabled();
  });

  it("disables 'Save for review' button when there are unresolved items", () => {
    const countsWithUnresolved = {
      ...defaultCounts,
      "?": 1,
      total: 1,
    };
    render(<ManagementForm counts={countsWithUnresolved} />);

    const saveForReviewButton = screen.getByRole("button", {
      name: "Save for review",
    });
    expect(saveForReviewButton).toBeDisabled();
  });

  it("enables 'Save for review' button when all items are resolved", () => {
    const countsWithAllResolved = {
      ...defaultCounts,
      "+": 1,
      "-": 1,
      total: 2,
    };
    render(<ManagementForm counts={countsWithAllResolved} />);

    const saveForReviewButton = screen.getByRole("button", {
      name: "Save for review",
    });
    expect(saveForReviewButton).toBeEnabled();
  });

  it("shows tooltip when hovering over disabled 'Save for review' button", async () => {
    const user = userEvent.setup();
    const countsWithUnresolved = {
      ...defaultCounts,
      "?": 1,
      total: 1,
    };
    render(<ManagementForm counts={countsWithUnresolved} />);

    const saveForReviewButton = screen.getByRole("button", {
      name: "Save for review",
    });
    await user.hover(saveForReviewButton);

    expect(
      screen.getByText(
        "You cannot save for review until all search results are included or excluded",
      ),
    ).toBeVisible();
  });

  it("shows discard confirmation modal when clicking discard button", async () => {
    const user = userEvent.setup();
    render(<ManagementForm counts={defaultCounts} />);

    const discardButton = screen.getByRole("button", {
      name: "Discard",
    });
    await user.click(discardButton);

    expect(
      screen.getByText("Are you sure you want to discard this draft?"),
    ).toBeVisible();
    expect(screen.getByText("Discard draft")).toBeVisible();
    expect(screen.getByText("Continue editing")).toBeVisible();
  });

  it("closes discard modal when clicking continue editing", async () => {
    const user = userEvent.setup();
    render(<ManagementForm counts={defaultCounts} />);

    const discardButton = screen.getByRole("button", {
      name: "Discard",
    });
    await user.click(discardButton);

    const continueEditingButton = screen.getByRole("button", {
      name: "Continue editing",
    });
    await user.click(continueEditingButton);

    expect(
      screen.queryByText("Are you sure you want to discard this draft?"),
    ).not.toBeInTheDocument();
  });

  it("includes CSRF token in all forms", async () => {
    const user = userEvent.setup();
    render(<ManagementForm counts={defaultCounts} />);

    let csrfInputs = screen.getAllByDisplayValue("test-csrf-token");
    expect(csrfInputs).toHaveLength(1); // One in main form
    csrfInputs.forEach((input) => {
      expect(input).toHaveAttribute("name", "csrfmiddlewaretoken");
      expect(input).toHaveAttribute("type", "hidden");
    });

    const discardButton = screen.getByRole("button", {
      name: "Discard",
    });
    await user.click(discardButton);

    csrfInputs = screen.getAllByDisplayValue("test-csrf-token");
    expect(csrfInputs).toHaveLength(2); // One in main form, one in modal form
    csrfInputs.forEach((input) => {
      expect(input).toHaveAttribute("name", "csrfmiddlewaretoken");
      expect(input).toHaveAttribute("type", "hidden");
    });
  });

  it("includes correct action values in forms", async () => {
    const user = userEvent.setup();
    const countsWithAllResolved = {
      ...defaultCounts,
      "+": 1,
      "-": 1,
      total: 2,
    };
    render(<ManagementForm counts={countsWithAllResolved} />);

    // Main form actions
    const saveForReviewButton = screen.getByRole("button", {
      name: "Save for review",
    });
    const saveDraftButton = screen.getByRole("button", {
      name: "Save draft",
    });

    expect(saveForReviewButton).toHaveAttribute("value", "save-for-review");
    expect(saveDraftButton).toHaveAttribute("value", "save-draft");

    // Modal form action
    const discardButton = screen.getByRole("button", {
      name: "Discard",
    });
    await user.click(discardButton);

    const discardDraftButton = screen.getByRole("button", {
      name: "Discard draft",
    });
    expect(discardDraftButton).toHaveAttribute("value", "discard");
  });
});
