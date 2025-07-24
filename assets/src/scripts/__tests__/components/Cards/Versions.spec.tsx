import "@testing-library/jest-dom";
import { render, screen } from "@testing-library/react";
import React from "react";
import { beforeEach, describe, expect, it } from "vitest";
import Versions, {
  type VersionProps,
} from "../../../components/Cards/Versions";

describe("Version Component", () => {
  const mockVersions: VersionProps[] = [
    {
      created_at: "2025-05-14T12:39:54.944Z",
      current: true,
      status: "draft",
      tag_or_hash: "05657fec",
      url: "/codelist/test-university/new-style-codelist/05657fec/",
    },
    {
      created_at: "2025-05-14T14:31:50.976Z",
      current: false,
      status: "under review",
      tag_or_hash: "1e74f321",
      url: "/codelist/test-university/new-style-codelist/1e74f321/",
    },
    {
      created_at: "2025-05-14T14:32:01.686Z",
      current: false,
      status: "published",
      tag_or_hash: "37846656",
      url: "/codelist/test-university/new-style-codelist/37846656/",
    },
  ];

  beforeEach(() => {
    const script = document.createElement("script");
    script.id = "versions";
    script.type = "application/json";
    script.textContent = JSON.stringify(mockVersions);
    document.body.appendChild(script);
  });

  it("renders the versions card with header", () => {
    render(<Versions />);
    expect(screen.getByRole("heading", { name: "Versions" })).toBeVisible();
  });

  it("renders all version items", () => {
    render(<Versions />);
    mockVersions.forEach((version) => {
      expect(screen.getByText(version.tag_or_hash)).toBeVisible();
    });
  });

  it("displays correct badge for published version", () => {
    render(<Versions />);
    const publishedBadge = screen.getByText("Published");
    expect(publishedBadge).toBeVisible();
    expect(publishedBadge).toHaveClass("badge-success");
    expect(publishedBadge.parentElement).toHaveTextContent(
      mockVersions[2].tag_or_hash,
    );
  });

  it("displays correct badge for under review version", () => {
    render(<Versions />);
    const reviewBadge = screen.getByText("Under review");
    expect(reviewBadge).toBeVisible();
    expect(reviewBadge).toHaveClass("badge-info");
    expect(reviewBadge.parentElement).toHaveTextContent(
      mockVersions[1].tag_or_hash,
    );
  });

  it("displays correct badge for draft version", () => {
    render(<Versions />);
    const draftBadge = screen.getByText("Draft");
    expect(draftBadge).toBeVisible();
    expect(draftBadge).toHaveClass("badge-light");
    expect(draftBadge.parentElement).toHaveTextContent(
      mockVersions[0].tag_or_hash,
    );
  });

  it("renders correct links for non-current versions", () => {
    render(<Versions />);
    const nonCurrentVersions = mockVersions.filter((v) => !v.current);

    nonCurrentVersions.forEach((version) => {
      const versionElement = screen.getByText(version.tag_or_hash).closest("a");
      expect(versionElement).toHaveAttribute("href", encodeURI(version.url));
    });
  });

  it("renders a valid created date and time for a version", () => {
    render(<Versions />);

    // Tests are run with UTC+1 to confirm JS date formatting is applied
    // correctly. Therefore these times are one hour ahead of the
    // created_at strings.
    const expectedTimes = ["13:39", "15:31", "15:32"];

    const versions = screen.getAllByRole("listitem");
    expect(versions).toHaveLength(expectedTimes.length);

    versions.forEach((version, index) => {
      expect(version).toHaveTextContent(
        `14 May 2025 at ${expectedTimes[index]}`,
      );
    });
  });
});
