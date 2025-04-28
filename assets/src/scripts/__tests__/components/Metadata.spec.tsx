import "@testing-library/jest-dom";
import { render, screen } from "@testing-library/react";
import React from "react";
import { expect, it } from "vitest";
import Metadata from "../../components/Metadata";

const mockData = {
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

it("renders all required metadata fields", () => {
  render(<Metadata data={mockData} />);

  expect(screen.getByText("Coding system").tagName).toBe("DT");
  expect(screen.getByText(mockData.coding_system_name).tagName).toBe("DD");
  expect(
    screen.getByText(mockData.coding_system_name).previousElementSibling,
  ).toBe(screen.getByText("Coding system"));

  const codingSystemRelease = `${mockData.coding_system_release.release_name} (${mockData.coding_system_release.valid_from})`;
  expect(screen.getByText("Coding system release").tagName).toBe("DT");
  expect(screen.getByText(codingSystemRelease).tagName).toBe("DD");
  expect(screen.getByText(codingSystemRelease).previousElementSibling).toBe(
    screen.getByText("Coding system release"),
  );

  expect(screen.getByText("Organisation").tagName).toBe("DT");
  expect(screen.getByText(mockData.organisation_name).tagName).toBe("DD");
  expect(
    screen.getByText(mockData.organisation_name).previousElementSibling,
  ).toBe(screen.getByText("Organisation"));

  expect(screen.getByText("Codelist ID").tagName).toBe("DT");
  expect(screen.getByText(mockData.codelist_full_slug).tagName).toBe("DD");
  expect(
    screen.getByText(mockData.codelist_full_slug).previousElementSibling,
  ).toBe(screen.getByText("Codelist ID"));

  expect(screen.getByText("Version ID").tagName).toBe("DT");
  expect(screen.getByText(mockData.hash).tagName).toBe("DD");
  expect(screen.getByText(mockData.hash).previousElementSibling).toBe(
    screen.getByText("Version ID"),
  );
});

it("handles empty organisation name", () => {
  const dataWithoutOrg = {
    ...mockData,
    organisation_name: "",
  };

  render(<Metadata data={dataWithoutOrg} />);

  // Organisation field should not be present
  expect(screen.queryByText("Organisation")).not.toBeInTheDocument();

  // Other fields should still be present
  expect(screen.getByText("Version ID").tagName).toBe("DT");
  expect(screen.getByText(mockData.hash).tagName).toBe("DD");
  expect(screen.getByText(mockData.hash).previousElementSibling).toBe(
    screen.getByText("Version ID"),
  );
});

it("handles empty valid_from date in coding system release", () => {
  const dataWithoutValidFrom = {
    ...mockData,
    coding_system_release: {
      release_name: "v1.0",
      valid_from: "",
    },
  };

  render(<Metadata data={dataWithoutValidFrom} />);

  expect(screen.getByText("Coding system release").tagName).toBe("DT");
  expect(
    screen.getByText(mockData.coding_system_release.release_name).tagName,
  ).toBe("DD");
  expect(
    screen.getByText(mockData.coding_system_release.release_name)
      .previousElementSibling,
  ).toBe(screen.getByText("Coding system release"));
  expect(
    screen.queryByText(mockData.coding_system_release.valid_from),
  ).not.toBeInTheDocument();
});
