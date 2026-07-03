import "@testing-library/jest-dom";
import { render, screen } from "@testing-library/react";
import React from "react";
import { expect, it } from "vitest";
import CodelistWarnings from "../../../components/Codelist/CodelistWarnings";

const termDifferences = {
  M770: {
    combined_2016: "Old term",
    who_2019: "New term",
  },
};

const movedCodes = [
  {
    title: "Pneumocystosis",
    comment: "",
    nhs2016: ["B59"],
    who2019: ["B485"],
  },
];

it("renders warnings for included affected codes", () => {
  render(
    <CodelistWarnings
      icd10TermDifferences={termDifferences}
      icd10MovedCodes={movedCodes}
      includedCodes={new Set(["M770", "B59"])}
    />,
  );

  expect(screen.getAllByRole("alert")).toHaveLength(2);
  expect(screen.getByText("Conflicting definitions detected")).toBeVisible();
  expect(
    screen.getByText("This ICD-10 codelist may be incomplete"),
  ).toBeVisible();
  expect(screen.getAllByText("B485").at(-1)).toHaveClass(
    "warning-code-token--missing",
  );
});

it("renders plural text for multiple affected terms and moved codes", () => {
  render(
    <CodelistWarnings
      icd10TermDifferences={{
        ...termDifferences,
        M771: {
          combined_2016: "Another old term",
          who_2019: "Another new term",
        },
      }}
      icd10MovedCodes={[
        {
          title: "Moved concept with multiple codes",
          comment: "",
          nhs2016: ["A1", "A2"],
          who2019: ["B1", "B2"],
        },
      ]}
      includedCodes={new Set(["M770", "M771", "A1"])}
    />,
  );

  expect(screen.getByText("2 codes")).toBeVisible();
  expect(
    screen.getByRole("columnheader", { name: "NHS 2016 codes" }),
  ).toBeInTheDocument();
  expect(
    screen.getByRole("columnheader", { name: "WHO 2019 codes" }),
  ).toBeInTheDocument();
  expect(screen.getAllByText("A2").at(-1)).toHaveClass(
    "warning-code-token--missing",
  );
  expect(screen.getAllByText("B2").at(-1)).toHaveClass(
    "warning-code-token--missing",
  );
});

it("updates when the included code set changes", () => {
  const { rerender } = render(
    <CodelistWarnings
      icd10TermDifferences={termDifferences}
      icd10MovedCodes={movedCodes}
      includedCodes={new Set(["M770", "B59"])}
    />,
  );

  expect(screen.getAllByRole("alert")).toHaveLength(2);

  rerender(
    <CodelistWarnings
      icd10TermDifferences={termDifferences}
      icd10MovedCodes={movedCodes}
      includedCodes={new Set(["B59", "B485"])}
    />,
  );

  expect(screen.queryAllByRole("alert")).toHaveLength(0);
});
