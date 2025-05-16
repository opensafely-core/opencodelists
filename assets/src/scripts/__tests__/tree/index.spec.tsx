import "@testing-library/jest-dom";
import React from "react";
import { expect, it, vi } from "vitest";

// Mock createRoot and render
const mockRender = vi.fn();
vi.mock("react-dom/client", () => ({
  createRoot: vi.fn(() => ({
    render: mockRender,
  })),
}));

// Mock getElementById
const mockContainer = document.createElement("div");
mockContainer.id = "tree-data";
vi.spyOn(document, "getElementById").mockImplementation((id) => {
  if (id === "tree-data") {
    return mockContainer;
  }
  return null;
});

it("renders the Container component when tree-data element exists", async () => {
  // Import the module to trigger the initialization code
  await import("../../tree");

  // Check that createRoot was called with the correct container
  const { createRoot } = await import("react-dom/client");
  expect(createRoot).toHaveBeenCalledWith(mockContainer);

  // Check that render was called with StrictMode and Container
  expect(mockRender).toHaveBeenCalled();
  const renderCall = mockRender.mock.calls[0][0];
  expect(renderCall.type).toBe(React.StrictMode);
  expect(renderCall.props.children.type.name).toBe("Container");
});
