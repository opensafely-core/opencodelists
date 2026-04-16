import "@testing-library/jest-dom";
import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import React from "react";
import { beforeEach, expect, it, vi } from "vitest";
import CodelistTab from "../../../components/Layout/CodelistTab";
import type { CodeToUsage, UsagePillDisplayOptions } from "../../../types";

interface MockContainerProps {
  codeToUsage: CodeToUsage;
  usagePillDisplayOptions: UsagePillDisplayOptions;
}

const mockContainer = vi.fn(
  ({ codeToUsage, usagePillDisplayOptions }: MockContainerProps) => (
    <div data-testid="mock-container">
      <span data-testid="usage-position">
        {usagePillDisplayOptions.position}
      </span>
      <span data-testid="usage-number-format">
        {usagePillDisplayOptions.numberFormat}
      </span>
      <span data-testid="usage-value">{String(codeToUsage["123"])}</span>
      <span data-testid="usage-count">{Object.keys(codeToUsage).length}</span>
    </div>
  ),
);

vi.mock("../../../components/Codelist/Container", () => ({
  default: (props: MockContainerProps) => mockContainer(props),
}));

vi.mock("../../../components/Codelist/EmptySearch", () => ({
  default: () => <div>Empty search</div>,
}));

beforeEach(() => {
  mockContainer.mockClear();
});

it("updates usage pill position and number format from the temporary controls", async () => {
  const user = userEvent.setup();

  render(
    <CodelistTab
      allCodes={["123"]}
      codeToStatus={{ "123": "+" }}
      codeToTerm={{ "123": "Example code" }}
      hierarchy={{} as never}
      isEditable
      resultsHeading="Results"
      treeTables={[["Example section", ["123"]]]}
      updateStatus={vi.fn()}
      usageData={{
        periods: ["2026-01"],
        byPeriod: {
          "2026-01": { "123": 12345 },
        },
        sourceByPeriod: {
          "2026-01": "https://example.test/releases/2026-01",
        },
      }}
      visiblePaths={new Set(["123"])}
    />,
  );

  expect(screen.getByTestId("usage-position")).toHaveTextContent("left");
  expect(screen.getByTestId("usage-number-format")).toHaveTextContent(
    "condensed",
  );
  expect(screen.getByTestId("usage-value")).toHaveTextContent("12345");
  expect(screen.getByTestId("usage-count")).toHaveTextContent("1");

  await user.click(screen.getByRole("radio", { name: "Right" }));
  expect(screen.getByTestId("usage-position")).toHaveTextContent("right");

  await user.click(screen.getByRole("radio", { name: "Full" }));
  expect(screen.getByTestId("usage-number-format")).toHaveTextContent("full");

  await user.click(screen.getByLabelText("Show usage values in results"));
  expect(screen.getByTestId("usage-count")).toHaveTextContent("0");
});
