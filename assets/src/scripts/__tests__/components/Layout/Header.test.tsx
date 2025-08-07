import "@testing-library/jest-dom";
import { render, screen } from "@testing-library/react";
import React from "react";
import { afterEach, beforeEach, describe, expect, it } from "vitest";
import Header from "../../../components/Layout/Header";
import { builder_config } from "../../fixtures/version_from_scratch.json";
import { cleanupScriptTags, setScript } from "../../utils";

describe("Header component", () => {
  const counts = {
    "!": 0,
    "(+)": 0,
    "(-)": 0,
    "+": 0,
    "-": 0,
    "?": 0,
    total: 0,
  };

  beforeEach(() => setScript("builder-config", builder_config));
  afterEach(() => cleanupScriptTags(["builder-config"]));

  it("renders the title with the provided name", () => {
    render(<Header counts={counts} />);
    expect(screen.getByText(builder_config.codelist.name)).toBeVisible();
  });

  it("renders the Draft badge", () => {
    render(<Header counts={counts} />);
    const badge = screen.getByText("Draft");
    expect(screen.getByText("Draft")).toBeVisible();
    expect(badge).toHaveClass("badge-secondary");
  });

  it("renders all required metadata fields", () => {
    render(<Header counts={counts} />);

    expect(screen.getByText("Coding system").tagName).toBe("DT");
    expect(screen.getByText(builder_config.coding_system.name).tagName).toBe(
      "DD",
    );
    expect(
      screen.getByText(builder_config.coding_system.name)
        .previousElementSibling,
    ).toBe(screen.getByText("Coding system"));

    const codingSystemRelease = `${builder_config.coding_system.release.name} (${builder_config.coding_system.release.valid_from_date})`;
    expect(screen.getByText("Coding system release").tagName).toBe("DT");
    expect(screen.getByText(codingSystemRelease).tagName).toBe("DD");
    expect(screen.getByText(codingSystemRelease).previousElementSibling).toBe(
      screen.getByText("Coding system release"),
    );

    expect(screen.getByText("Organisation").tagName).toBe("DT");
    expect(screen.getByText(builder_config.codelist.organisation).tagName).toBe(
      "DD",
    );
    expect(
      screen.getByText(builder_config.codelist.organisation)
        .previousElementSibling,
    ).toBe(screen.getByText("Organisation"));

    expect(screen.getByText("Codelist ID").tagName).toBe("DT");
    expect(screen.getByText(builder_config.codelist.full_slug).tagName).toBe(
      "DD",
    );
    expect(
      screen.getByText(builder_config.codelist.full_slug)
        .previousElementSibling,
    ).toBe(screen.getByText("Codelist ID"));

    expect(screen.getByText("Version ID").tagName).toBe("DT");
    expect(screen.getByText(builder_config.codelist.hash).tagName).toBe("DD");
    expect(
      screen.getByText(builder_config.codelist.hash).previousElementSibling,
    ).toBe(screen.getByText("Version ID"));
  });

  it("handles empty organisation name", () => {
    cleanupScriptTags(["builder-config"]);

    setScript("builder-config", {
      ...builder_config,
      codelist: { ...builder_config.codelist, organisation: "" },
    });

    render(<Header counts={counts} />);

    // Organisation field should not be present
    expect(screen.queryByText("Organisation")).not.toBeInTheDocument();

    // Other fields should still be present
    expect(screen.getByText("Version ID").tagName).toBe("DT");
    expect(screen.getByText(builder_config.codelist.hash).tagName).toBe("DD");
    expect(
      screen.getByText(builder_config.codelist.hash).previousElementSibling,
    ).toBe(screen.getByText("Version ID"));
  });

  it("handles empty valid_from date in coding system release", () => {
    cleanupScriptTags(["builder-config"]);

    setScript("builder-config", {
      ...builder_config,
      coding_system: {
        ...builder_config.coding_system,
        release: { name: "v1.0", valid_from_date: null },
      },
    });

    render(<Header counts={counts} />);

    expect(screen.getByText("Coding system release").tagName).toBe("DT");
    expect(screen.getByText("v1.0").tagName).toBe("DD");
    expect(screen.getByText("v1.0").previousElementSibling).toBe(
      screen.getByText("Coding system release"),
    );
  });
});
