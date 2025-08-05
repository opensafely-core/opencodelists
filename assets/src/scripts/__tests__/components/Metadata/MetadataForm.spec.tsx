import "@testing-library/jest-dom";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import nock from "nock";
import React, { type ReactNode } from "react";
import { afterEach, beforeEach, describe, expect, it } from "vitest";
import MetadataForm from "../../../components/Metadata/MetadataForm";
import type { IS_EDITABLE, METADATA, UPDATE_URL } from "../../../types";

const queryClient = new QueryClient({
  defaultOptions: { queries: { retry: false } },
});
const wrapper = ({ children }: { children: ReactNode }) => (
  <QueryClientProvider client={queryClient}>{children}</QueryClientProvider>
);

// biome-ignore lint/suspicious/noExplicitAny: we can pass in any data in this test
function setScript(id: string, value: any) {
  const el = document.createElement("script");
  el.id = id;
  el.type = "application/json";
  el.textContent = JSON.stringify(value);
  document.body.appendChild(el);
}

function scriptTagSetup({
  metadata,
  isEditable = true,
  updateUrl = "https://mock-url.localhost/update",
}: {
  metadata?: {
    description?: METADATA["description"];
    methodology?: METADATA["methodology"];
  };
  isEditable?: IS_EDITABLE;
  updateUrl?: UPDATE_URL;
} = {}) {
  setScript("metadata", metadata);
  setScript("is-editable", isEditable);
  setScript("update-url", updateUrl);
}

function cleanupScriptTags() {
  ["metadata", "update-url", "is-editable"].forEach((id) =>
    document.getElementById(id)?.remove(),
  );
}

function mockPostRequest(metadata: {
  description: { html: string; text: string };
}) {
  return nock("https://mock-url.localhost")
    .post("/update")
    .reply(200, { metadata });
}

describe("Does not load", () => {
  beforeEach(() => scriptTagSetup());
  afterEach(() => cleanupScriptTags());

  it("does not show if no data is provided", () => {
    render(<MetadataForm id="description" name="Description" />, { wrapper });
    expect(
      screen.queryByRole("heading", { name: "Description" }),
    ).not.toBeInTheDocument();
  });
});

describe("Anonymous users", () => {
  beforeEach(() => {
    queryClient.clear();
    scriptTagSetup({
      isEditable: false,
      metadata: {
        description: {
          text: "This is a test",
          html: "<p>This is a test</p>",
        },
      },
    });
  });
  afterEach(() => cleanupScriptTags());

  it("does not show buttons to anonymous users", () => {
    render(<MetadataForm id="description" name="Description" />, { wrapper });
    expect(
      screen.queryByRole("heading", { name: "Description" }),
    ).toBeVisible();
    expect(
      screen.queryByRole("button", { name: "Edit Description" }),
    ).not.toBeInTheDocument();
  });
});

describe("Interacting with Metadata forms", () => {
  beforeEach(() => {
    queryClient.clear();
    scriptTagSetup({
      isEditable: true,
      metadata: {
        description: {
          text: "This is a test",
          html: "<p>This is a test</p>",
        },
        methodology: {
          text: "This is a test",
          html: "<p>This is a test</p>",
        },
      },
    });
  });

  afterEach(() => cleanupScriptTags());

  it("loads the HTML text from the metadata", async () => {
    render(<MetadataForm id="description" name="Description" />, { wrapper });
    expect(screen.getByText("This is a test")).toBeVisible();
  });

  it("loads the buttons for users who can edit", async () => {
    render(<MetadataForm id="methodology" name="Methodology" />, { wrapper });
    expect(
      screen.getByRole("button", { name: "Edit Methodology" }),
    ).toBeVisible();
  });

  it("opens and closes the editing view, discarding changes", async () => {
    const user = userEvent.setup();
    render(<MetadataForm id="description" name="Description" />, { wrapper });

    await waitFor(() => {
      expect(
        screen.getByRole("button", { name: "Edit Description" }),
      ).toBeVisible();
    });

    await user.click(screen.getByRole("button", { name: "Edit Description" }));
    expect(screen.getByRole("textbox", { name: "Description" })).toBeVisible();
    expect(screen.getByRole("textbox", { name: "Description" })).toHaveValue(
      "This is a test",
    );
    await user.click(screen.getByRole("button", { name: "Cancel" }));
    expect(
      screen.queryByRole("textbox", { name: "Description" }),
    ).not.toBeInTheDocument();

    await user.click(screen.getByRole("button", { name: "Edit Description" }));
    await user.clear(screen.getByRole("textbox", { name: "Description" }));
    await user.type(
      screen.getByRole("textbox", { name: "Description" }),
      "This is some text which is going to be discarded",
    );
    await user.click(screen.getByRole("button", { name: "Cancel" }));
    expect(
      screen.queryByRole("textbox", { name: "Description" }),
    ).not.toBeInTheDocument();
    expect(screen.getByText("This is a test")).toBeVisible();
  });

  it("allows editing of content", async () => {
    const user = userEvent.setup();
    mockPostRequest({
      description: {
        html: "<p>This is some text which is going to be saved</p>",
        text: "This is some text which is going to be saved",
      },
    });
    render(<MetadataForm id="description" name="Description" />, { wrapper });

    await waitFor(() => {
      expect(
        screen.getByRole("button", { name: "Edit Description" }),
      ).toBeVisible();
    });

    await user.click(screen.getByRole("button", { name: "Edit Description" }));
    expect(screen.getByRole("textbox", { name: "Description" })).toBeVisible();
    expect(screen.getByRole("textbox", { name: "Description" })).toHaveValue(
      "This is a test",
    );
    await user.click(screen.getByRole("button", { name: "Cancel" }));
    expect(
      screen.queryByRole("textbox", { name: "Description" }),
    ).not.toBeInTheDocument();

    await user.click(screen.getByRole("button", { name: "Edit Description" }));
    await user.clear(screen.getByRole("textbox", { name: "Description" }));
    await user.type(
      screen.getByRole("textbox", { name: "Description" }),
      "This is some text which is going to be saved",
    );
    await user.click(screen.getByRole("button", { name: "Save" }));

    await waitFor(() =>
      expect(
        screen.getByText("This is some text which is going to be saved"),
      ).toBeVisible(),
    );
  });

  it("accepts keyboard shortcuts to cancel", async () => {
    const user = userEvent.setup();
    mockPostRequest({
      description: {
        html: "<p>This is some text which is going to be saved</p>",
        text: "This is some text which is going to be saved",
      },
    });
    render(<MetadataForm id="description" name="Description" />, { wrapper });

    await waitFor(() => {
      expect(
        screen.getByRole("button", { name: "Edit Description" }),
      ).toBeVisible();
    });

    await user.click(screen.getByRole("button", { name: "Edit Description" }));
    expect(screen.getByRole("textbox", { name: "Description" })).toBeVisible();
    expect(screen.getByRole("textbox", { name: "Description" })).toHaveValue(
      "This is a test",
    );
    await user.clear(screen.getByRole("textbox", { name: "Description" }));
    await user.type(
      screen.getByRole("textbox", { name: "Description" }),
      "This is some text which is going to be discarded",
    );
    await user.keyboard("[Escape]");
    await waitFor(() => {
      expect(
        screen.queryByRole("textbox", { name: "Description" }),
      ).not.toBeInTheDocument();
      expect(screen.getByText("This is a test")).toBeVisible();
    });
  });

  it("allows keyboard shortcuts to save", async () => {
    const user = userEvent.setup();
    mockPostRequest({
      description: {
        html: "<p>This is some text which is going to be saved</p>",
        text: "This is some text which is going to be saved",
      },
    });
    render(<MetadataForm id="description" name="Description" />, { wrapper });

    await waitFor(() => {
      expect(
        screen.getByRole("button", { name: "Edit Description" }),
      ).toBeVisible();
    });

    await user.click(screen.getByRole("button", { name: "Edit Description" }));
    expect(screen.getByRole("textbox", { name: "Description" })).toBeVisible();
    expect(screen.getByRole("textbox", { name: "Description" })).toHaveValue(
      "This is a test",
    );
    await user.click(screen.getByRole("button", { name: "Cancel" }));
    expect(
      screen.queryByRole("textbox", { name: "Description" }),
    ).not.toBeInTheDocument();

    await user.click(screen.getByRole("button", { name: "Edit Description" }));
    await user.clear(screen.getByRole("textbox", { name: "Description" }));
    await user.type(
      screen.getByRole("textbox", { name: "Description" }),
      "This is some text which is going to be saved",
    );
    await user.keyboard("{Meta>}[Enter]");

    await waitFor(() =>
      expect(
        screen.getByText("This is some text which is going to be saved"),
      ).toBeVisible(),
    );
  });
});

describe("Empty metadata", () => {
  beforeEach(() => {
    queryClient.clear();
  });
  afterEach(() => cleanupScriptTags());

  it("renders the not provided message when no HTML is available", () => {
    scriptTagSetup({
      isEditable: true,
      metadata: {
        description: {
          text: "This is a test",
          html: "",
        },
      },
    });
    render(<MetadataForm id="description" name="Description" />, { wrapper });

    expect(screen.getByText("Description not provided")).toBeVisible();
  });

  it("renders the `not provided` message when no text is available", () => {
    scriptTagSetup({
      isEditable: true,
      metadata: {
        description: {
          text: "",
          html: "<p></p>",
        },
      },
    });
    render(<MetadataForm id="description" name="Description" />, { wrapper });

    expect(screen.getByText("Description not provided")).toBeVisible();
  });
});
