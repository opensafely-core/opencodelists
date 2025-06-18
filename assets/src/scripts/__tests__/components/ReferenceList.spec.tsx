import "@testing-library/jest-dom";
import { render, screen } from "@testing-library/react";
import React from "react";
import { describe, expect, it } from "vitest";
import ReferenceList from "../../components/ReferenceList";
import { Reference } from "../../types";

describe("ReferenceList Component - empty list", () => {
  it("renders an add button for empty list", () => {
    render(<ReferenceList references={[]} onSave={() => null} />);
    expect(screen.getByText("Add a reference")).toBeInTheDocument();
  });
});

describe("ReferenceList Component - non-empty list", () => {
  const mockReferences: Reference[] = [
    {
      text: "Link 1",
      url: "https://example.com/link1",
    },
    {
      text: "Link 2",
      url: "https://example.com/link2",
    },
  ];

  it("renders a list of references", () => {
    render(<ReferenceList references={mockReferences} onSave={() => null} />);
    for (const ref of mockReferences) {
      const link = document.querySelector(`a[href="${ref.url}"]`);
      expect(link).toBeInTheDocument();
      expect(link).toHaveTextContent(ref.text);
    }
  });

  it("displays an add button", () => {
    render(<ReferenceList references={mockReferences} onSave={() => null} />);
    expect(screen.getByText("Add another reference")).toBeInTheDocument();
  });
});
