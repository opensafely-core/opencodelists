import "@testing-library/jest-dom";
import React from "react";
import { beforeEach, expect, it, vi } from "vitest";

const mockRender = vi.fn();
const createRootMock = vi.fn(() => ({
  render: mockRender,
}));

vi.mock("react-dom/client", () => ({
  createRoot: createRootMock,
}));

beforeEach(() => {
  vi.resetModules();
  mockRender.mockClear();
  createRootMock.mockClear();
  document.body.innerHTML = "";
});

it("mounts the codelist warnings component when the page container exists", async () => {
  document.body.innerHTML = `
    <div id="codelist-warnings"></div>
    <script id="icd10-term-differences" type="application/json">
      {"M770":{"combined_2016":"Old term","who_2019":"New term"}}
    </script>
    <script id="icd10-moved-codes" type="application/json">
      [{"title":"Moved concept","nhs2016":["B59"],"who2019":["B485"],"comment":""}]
    </script>
    <script id="included-codes" type="application/json">["M770","B59"]</script>
  `;

  await import("../codelist-warnings");

  expect(createRootMock).toHaveBeenCalledWith(
    document.getElementById("codelist-warnings"),
  );
  expect(mockRender).toHaveBeenCalled();

  const renderCall = mockRender.mock.calls[0][0];
  expect(renderCall.type).toBe(React.StrictMode);
  expect(renderCall.props.children.type.name).toBe("CodelistWarnings");
  expect(renderCall.props.children.props.includedCodes).toEqual(
    new Set(["M770", "B59"]),
  );
});

it("does not mount the codelist warnings component when the page container does not exist", async () => {
  document.body.innerHTML = `
    <script id="icd10-term-differences" type="application/json">
      {"M770":{"combined_2016":"Old term","who_2019":"New term"}}
    </script>
    <script id="icd10-moved-codes" type="application/json">
      [{"title":"Moved concept","nhs2016":["B59"],"who2019":["B485"],"comment":""}]
    </script>
    <script id="included-codes" type="application/json">["M770","B59"]</script>
  `;

  await import("../codelist-warnings");

  expect(createRootMock).not.toHaveBeenCalled();
  expect(mockRender).not.toHaveBeenCalled();
});
