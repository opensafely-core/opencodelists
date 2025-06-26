import "@testing-library/jest-dom";
import { render, screen } from "@testing-library/react";
import React from "react";
import { afterEach, describe, expect, it, vi } from "vitest";
import Tools from "../../../components/Cards/Tools";

vi.mock("../../../data/tools.json", () => ({
  default: [
    {
      codingSystem: ["icd10", "snomedct"],
      description: "ICD10/SNOMED tool description.",
      id: "tool-1",
      link: "https://example.com/tool-1",
      name: "Tool 1",
    },
    {
      codingSystem: ["bnf"],
      description: "BNF tool description.",
      id: "tool-2",
      link: "https://example.com/tool-2",
      name: "Tool 2",
    },
  ],
}));

describe("<Tools />", () => {
  afterEach(() => {
    const script = document.getElementById("metadata");
    if (script) script.remove();
  });

  it("returns null if coding system is not present", async () => {
    const { container } = render(<Tools />);
    expect(container.firstChild).toBeNull();
  });

  it("returns null if no tools for coding system", async () => {
    const script = document.createElement("script");
    script.id = "metadata";
    script.type = "application/json";
    script.textContent = JSON.stringify({
      coding_system_id: "ctv3",
    });
    document.body.appendChild(script);

    const { container } = render(<Tools />);
    expect(container.firstChild).toBeNull();
  });

  it("renders tools for icd10", async () => {
    const script = document.createElement("script");
    script.id = "metadata";
    script.type = "application/json";
    script.textContent = JSON.stringify({ coding_system_id: "icd10" });
    document.body.appendChild(script);

    render(<Tools />);
    expect(screen.getByRole("heading", { name: "Tools" })).toBeVisible();
    expect(
      screen.getByText(
        "Tools to help you to build a better and more accurate codelist.",
      ),
    ).toBeVisible();

    // Only Tool 1 should be shown
    const link = screen.getByRole("link", { name: "Tool 1" });
    expect(link).toHaveAttribute("href", "https://example.com/tool-1");
    expect(screen.getByText("ICD10/SNOMED tool description.")).toBeVisible();

    // Tool 2 should not be present
    expect(screen.queryByText("Tool 2")).toBeNull();
  });

  it("renders tools for BNF", async () => {
    const script = document.createElement("script");
    script.id = "metadata";
    script.type = "application/json";
    script.textContent = JSON.stringify({ coding_system_id: "bnf" });
    document.body.appendChild(script);

    render(<Tools />);
    expect(screen.getByRole("heading", { name: "Tools" })).toBeVisible();

    // Only Tool 2 should be shown
    const link = screen.getByRole("link", { name: "Tool 2" });
    expect(link).toHaveAttribute("href", "https://example.com/tool-2");
    expect(screen.getByText("BNF tool description.")).toBeVisible();

    // Tool 1 should not be present
    expect(screen.queryByText("Tool 1")).toBeNull();
  });
});
