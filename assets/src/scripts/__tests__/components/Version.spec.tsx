import "@testing-library/jest-dom";
import { render, screen } from "@testing-library/react";
import React from "react";
import { describe, expect, it } from "vitest";
import Version from "../../components/Version";
import { VersionT } from "../../types";

describe("Version Component", () => {
  const mockVersions: VersionT[] = [
    {
      current: true,
      status: "draft",
      tag_or_hash: "05657fec",
      url: "/codelist/test-university/new-style-codelist/05657fec/",
    },
    {
      current: false,
      status: "under review",
      tag_or_hash: "1e74f321",
      url: "/codelist/test-university/new-style-codelist/1e74f321/",
    },
    {
      current: false,
      status: "published",
      tag_or_hash: "37846656",
      url: "/codelist/test-university/new-style-codelist/37846656/",
    },
  ];

  it("renders the versions card with header", () => {
    render(<Version versions={mockVersions} />);
    expect(screen.getByRole("heading", { name: "Versions" })).toBeVisible();
  });

  it("renders all version items", () => {
    render(<Version versions={mockVersions} />);
    mockVersions.forEach((version) => {
      expect(screen.getByText(version.tag_or_hash)).toBeVisible();
    });
  });

  it("displays correct badge for published version", () => {
    render(<Version versions={mockVersions} />);
    const publishedBadge = screen.getByText("Published");
    expect(publishedBadge).toBeVisible();
    expect(publishedBadge).toHaveClass("badge-success");
    expect(publishedBadge.parentElement).toHaveTextContent(
      mockVersions[2].tag_or_hash,
    );
  });

  it("displays correct badge for under review version", () => {
    render(<Version versions={mockVersions} />);
    const reviewBadge = screen.getByText("Under review");
    expect(reviewBadge).toBeVisible();
    expect(reviewBadge).toHaveClass("badge-info");
    expect(reviewBadge.parentElement).toHaveTextContent(
      mockVersions[1].tag_or_hash,
    );
  });

  it("displays correct badge for draft version", () => {
    render(<Version versions={mockVersions} />);
    const draftBadge = screen.getByText("Draft");
    expect(draftBadge).toBeVisible();
    expect(draftBadge).toHaveClass("badge-light");
    expect(draftBadge.parentElement).toHaveTextContent(
      mockVersions[0].tag_or_hash,
    );
  });

  it("marks current version as active and disabled", () => {
    render(<Version versions={mockVersions} />);
    const currentVersion = screen
      .getByText(mockVersions[0].tag_or_hash)
      .closest("a");
    expect(currentVersion).toHaveClass("active disabled");
  });

  it("renders correct links for non-current versions", () => {
    render(<Version versions={mockVersions} />);
    const nonCurrentVersions = mockVersions.filter((v) => !v.current);

    nonCurrentVersions.forEach((version) => {
      const versionElement = screen.getByText(version.tag_or_hash).closest("a");
      expect(versionElement).toHaveAttribute("href", encodeURI(version.url));
    });
  });
});
