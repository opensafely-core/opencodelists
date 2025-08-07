import "@testing-library/jest-dom";
import { render, screen } from "@testing-library/react";
import React from "react";
import { afterEach, describe, expect, it, vi } from "vitest";
import Tools from "../../../components/Cards/Tools";
import { builder_config } from "../../fixtures/version_from_scratch.json";
import { cleanupScriptTags, setScript } from "../../utils";

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
  afterEach(() => cleanupScriptTags(["builder-config"]));

  it("returns null if coding system is not present", async () => {
    setScript("builder-config", { ...builder_config, coding_system: {} });
    const { container } = render(<Tools />);
    expect(container.firstChild).toBeNull();
  });

  it("returns null if no tools for coding system", async () => {
    setScript("builder-config", {
      ...builder_config,
      coding_system: { ...builder_config.coding_system, id: "ctv3" },
    });
    const { container } = render(<Tools />);
    expect(container.firstChild).toBeNull();
  });

  it("renders tools for icd10", async () => {
    setScript("builder-config", {
      ...builder_config,
      coding_system: { ...builder_config.coding_system, id: "icd10" },
    });

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
    setScript("builder-config", {
      ...builder_config,
      coding_system: { ...builder_config.coding_system, id: "bnf" },
    });

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
