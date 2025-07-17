import "@testing-library/jest-dom";
import { render, screen } from "@testing-library/react";
import React from "react";
import { describe, expect, it } from "vitest";
import Header from "../../../components/Layout/Header";

describe("Header component", () => {
  const metadata = {
    coding_system_id: "test",
    coding_system_name: "Test Coding System",
    coding_system_release: {
      release_name: "v1.0",
      valid_from: "2024-01-01",
    },
    organisation_name: "Test Organisation",
    codelist_full_slug: "test/codelist",
    codelist_name: "Test Codelist",
    draft: false,
    hash: "abc123",
  };
  const isEditable = true;
  const counts = {
    "!": 0,
    "(+)": 0,
    "(-)": 0,
    "+": 0,
    "-": 0,
    "?": 0,
    total: 0,
  };

  it("renders the title with the provided name", () => {
    render(
      <Header isEditable={isEditable} counts={counts} metadata={metadata} />,
    );
    expect(screen.getByText(metadata.codelist_name)).toBeVisible();
  });

  it("renders the Draft badge", () => {
    render(
      <Header isEditable={isEditable} counts={counts} metadata={metadata} />,
    );
    const badge = screen.getByText("Draft");
    expect(screen.getByText("Draft")).toBeVisible();
    expect(badge).toHaveClass("badge-secondary");
  });

  it("renders all required metadata fields", () => {
    render(
      <Header isEditable={isEditable} counts={counts} metadata={metadata} />,
    );

    expect(screen.getByText("Coding system").tagName).toBe("DT");
    expect(screen.getByText(metadata.coding_system_name).tagName).toBe("DD");
    expect(
      screen.getByText(metadata.coding_system_name).previousElementSibling,
    ).toBe(screen.getByText("Coding system"));

    const codingSystemRelease = `${metadata.coding_system_release.release_name} (${metadata.coding_system_release.valid_from})`;
    expect(screen.getByText("Coding system release").tagName).toBe("DT");
    expect(screen.getByText(codingSystemRelease).tagName).toBe("DD");
    expect(screen.getByText(codingSystemRelease).previousElementSibling).toBe(
      screen.getByText("Coding system release"),
    );

    expect(screen.getByText("Organisation").tagName).toBe("DT");
    expect(screen.getByText(metadata.organisation_name).tagName).toBe("DD");
    expect(
      screen.getByText(metadata.organisation_name).previousElementSibling,
    ).toBe(screen.getByText("Organisation"));

    expect(screen.getByText("Codelist ID").tagName).toBe("DT");
    expect(screen.getByText(metadata.codelist_full_slug).tagName).toBe("DD");
    expect(
      screen.getByText(metadata.codelist_full_slug).previousElementSibling,
    ).toBe(screen.getByText("Codelist ID"));

    expect(screen.getByText("Version ID").tagName).toBe("DT");
    expect(screen.getByText(metadata.hash).tagName).toBe("DD");
    expect(screen.getByText(metadata.hash).previousElementSibling).toBe(
      screen.getByText("Version ID"),
    );
  });

  it("handles empty organisation name", () => {
    const dataWithoutOrg = {
      ...metadata,
      organisation_name: "",
    };

    render(
      <Header
        isEditable={isEditable}
        counts={counts}
        metadata={dataWithoutOrg}
      />,
    );

    // Organisation field should not be present
    expect(screen.queryByText("Organisation")).not.toBeInTheDocument();

    // Other fields should still be present
    expect(screen.getByText("Version ID").tagName).toBe("DT");
    expect(screen.getByText(metadata.hash).tagName).toBe("DD");
    expect(screen.getByText(metadata.hash).previousElementSibling).toBe(
      screen.getByText("Version ID"),
    );
  });

  it("handles empty valid_from date in coding system release", () => {
    const dataWithoutValidFrom = {
      ...metadata,
      coding_system_release: {
        release_name: "v1.0",
        valid_from: "",
      },
    };

    render(
      <Header
        isEditable={isEditable}
        counts={counts}
        metadata={dataWithoutValidFrom}
      />,
    );

    expect(screen.getByText("Coding system release").tagName).toBe("DT");
    expect(
      screen.getByText(metadata.coding_system_release.release_name).tagName,
    ).toBe("DD");
    expect(
      screen.getByText(metadata.coding_system_release.release_name)
        .previousElementSibling,
    ).toBe(screen.getByText("Coding system release"));
    expect(
      screen.queryByText(metadata.coding_system_release.valid_from),
    ).not.toBeInTheDocument();
  });
});
