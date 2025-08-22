import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import React, { type ReactNode } from "react";
import "@testing-library/jest-dom";
import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import nock from "nock";
import { afterEach, beforeEach, describe, expect, it } from "vitest";
import References from "../../../components/Metadata/References";

type Reference = { text: string; url: string };

const wrapper = ({ children }: { children: ReactNode }) => {
  const queryClient = new QueryClient({
    defaultOptions: { queries: { retry: false } },
  });

  return (
    <QueryClientProvider client={queryClient}>{children}</QueryClientProvider>
  );
};

// biome-ignore lint/suspicious/noExplicitAny: we can pass in any data in this test
function setScript(id: string, value: any) {
  const el = document.createElement("script");
  el.id = id;
  el.type = "application/json";
  el.textContent = JSON.stringify(value);
  document.body.appendChild(el);
}

function scriptTagSetup({
  references = [],
  isEditable = true,
  updateUrl = "https://mock-url.localhost/update",
}: {
  references?: Reference[];
  isEditable?: boolean;
  updateUrl?: string;
} = {}) {
  setScript("metadata", { references });
  setScript("is-editable", isEditable);
  setScript("update-url", updateUrl);
}

function cleanupScriptTags() {
  ["metadata", "update-url", "is-editable"].forEach((id) => {
    document.getElementById(id)?.remove();
  });
}

function mockPostRequest(references: Reference[]) {
  return nock("https://mock-url.localhost")
    .post("/update")
    .reply(200, { metadata: { references } });
}

describe("Metadata tab references", () => {
  it("does not display if references is not available on the page", () => {
    render(<References />, { wrapper });
    expect(
      screen.queryByRole("heading", { name: "References" }),
    ).not.toBeInTheDocument();
  });

  describe("Add new references", () => {
    beforeEach(() => scriptTagSetup());
    afterEach(() => cleanupScriptTags());

    it("displays the add reference button", async () => {
      render(<References />, { wrapper });

      await waitFor(() => {
        expect(
          screen.getByRole("button", { name: "Add a reference" }),
        ).toBeInTheDocument();
      });
    });

    it("displays an empty form when the add reference button is clicked", async () => {
      const user = userEvent.setup();
      render(<References />, { wrapper });

      await waitFor(() => {
        expect(
          screen.getByRole("button", { name: "Add a reference" }),
        ).toBeInTheDocument();
      });

      await user.click(screen.getByRole("button", { name: "Add a reference" }));
      expect(screen.getByRole("textbox", { name: "Text" })).toBeVisible();
      expect(screen.getByRole("textbox", { name: "Text" })).toHaveValue("");
      expect(screen.getByRole("textbox", { name: "URL" })).toBeVisible();
      expect(screen.getByRole("textbox", { name: "URL" })).toHaveValue("");
    });

    it("closes the form edit view if a user opens it, then presses cancel", async () => {
      const user = userEvent.setup();
      render(<References />, { wrapper });

      await waitFor(() => {
        expect(
          screen.getByRole("button", { name: "Add a reference" }),
        ).toBeInTheDocument();
      });
      await user.click(screen.getByRole("button", { name: "Add a reference" }));
      expect(screen.getByRole("textbox", { name: "Text" })).toBeVisible();
      await user.click(screen.getByRole("button", { name: "Cancel" }));
      expect(
        screen.queryByRole("textbox", { name: "Text" }),
      ).not.toBeInTheDocument();
      expect(
        screen.queryByRole("textbox", { name: "URL" }),
      ).not.toBeInTheDocument();
    });
  });

  describe("Existing references", () => {
    beforeEach(() =>
      scriptTagSetup({
        references: [{ text: "Google", url: "https://www.google.com" }],
      }),
    );
    afterEach(() => cleanupScriptTags());

    it("displays add another reference button", async () => {
      render(<References />, { wrapper });

      await waitFor(() => {
        expect(
          screen.getByRole("button", { name: "Add another reference" }),
        ).toBeInTheDocument();
      });
    });

    it("returns a link to a reference", async () => {
      render(<References />, { wrapper });

      await waitFor(() => {
        expect(
          screen.getByRole("button", { name: "Add another reference" }),
        ).toBeInTheDocument();
      });
      expect(screen.getByRole("link", { name: "Google" })).toBeInTheDocument();
      expect(screen.getByRole("link", { name: "Google" })).toHaveAttribute(
        "href",
        "https://www.google.com",
      );
    });

    it("contains buttons for editing or deleting for codelist owner", async () => {
      render(<References />, { wrapper });

      await waitFor(() => {
        expect(
          screen.getByRole("button", { name: "Add another reference" }),
        ).toBeInTheDocument();
      });
      expect(screen.queryByRole("button", { name: "Edit" })).toBeVisible();
      expect(screen.queryByRole("button", { name: "Delete" })).toBeVisible();
    });

    it("shows a form when the user clicks edit", async () => {
      const user = userEvent.setup();
      render(<References />, { wrapper });

      await waitFor(() => {
        expect(
          screen.getByRole("button", { name: "Add another reference" }),
        ).toBeInTheDocument();
      });
      await user.click(screen.getByRole("button", { name: "Edit" }));
      expect(screen.getByRole("textbox", { name: "Text" })).toBeVisible();
      expect(screen.getByRole("textbox", { name: "URL" })).toBeVisible();
    });

    it("shows the users existing data in the form when they click edit", async () => {
      const user = userEvent.setup();
      render(<References />, { wrapper });

      await waitFor(() => {
        expect(
          screen.getByRole("button", { name: "Add another reference" }),
        ).toBeInTheDocument();
      });
      await user.click(screen.getByRole("button", { name: "Edit" }));
      expect(screen.getByRole("textbox", { name: "Text" })).toHaveValue(
        "Google",
      );
      expect(screen.getByRole("textbox", { name: "URL" })).toHaveValue(
        "https://www.google.com",
      );
    });

    it("closes the form edit view if a user opens it, then presses cancel", async () => {
      const user = userEvent.setup();
      render(<References />, { wrapper });

      await waitFor(() => {
        expect(
          screen.getByRole("button", { name: "Edit" }),
        ).toBeInTheDocument();
      });
      await user.click(screen.getByRole("button", { name: "Edit" }));
      expect(screen.getByRole("textbox", { name: "Text" })).toBeVisible();
      expect(screen.getByRole("textbox", { name: "URL" })).toBeVisible();
      await user.click(screen.getByRole("button", { name: "Cancel" }));
      expect(
        screen.queryByRole("textbox", { name: "Text" }),
      ).not.toBeInTheDocument();
      expect(
        screen.queryByRole("textbox", { name: "URL" }),
      ).not.toBeInTheDocument();
    });

    it("closes the form edit view if a user opens it, then presses ESCAPE", async () => {
      const user = userEvent.setup();
      render(<References />, { wrapper });

      await waitFor(() => {
        expect(
          screen.getByRole("button", { name: "Edit" }),
        ).toBeInTheDocument();
      });
      await user.click(screen.getByRole("button", { name: "Edit" }));
      expect(screen.getByRole("textbox", { name: "Text" })).toBeVisible();
      expect(screen.getByRole("textbox", { name: "URL" })).toBeVisible();
      await user.keyboard("{Escape}");
      expect(
        screen.queryByRole("textbox", { name: "Text" }),
      ).not.toBeInTheDocument();
      expect(
        screen.queryByRole("textbox", { name: "URL" }),
      ).not.toBeInTheDocument();
    });
  });

  describe("Anonymous users", () => {
    beforeEach(() =>
      scriptTagSetup({
        references: [{ text: "Google", url: "https://www.google.com" }],
        isEditable: false,
      }),
    );
    afterEach(() => cleanupScriptTags());

    it("does not contain buttons for adding for anonymous users", async () => {
      render(<References />, { wrapper });
      await waitFor(() => {
        expect(
          screen.getByRole("heading", { name: "References" }),
        ).toBeInTheDocument();
      });
      expect(
        screen.queryByRole("button", { name: "Add a reference" }),
      ).not.toBeInTheDocument();
      expect(
        screen.queryByRole("button", { name: "Add another reference" }),
      ).not.toBeInTheDocument();
    });

    it("does not contain buttons for editing or deleting for anonymous users", async () => {
      render(<References />, { wrapper });
      await waitFor(() => {
        expect(
          screen.getByRole("heading", { name: "References" }),
        ).toBeInTheDocument();
      });
      expect(
        screen.queryByRole("button", { name: "Edit" }),
      ).not.toBeInTheDocument();
      expect(
        screen.queryByRole("button", { name: "Delete" }),
      ).not.toBeInTheDocument();
    });
  });

  describe("Updating state", () => {
    beforeEach(() =>
      scriptTagSetup({
        references: [{ text: "Google", url: "https://www.google.com" }],
        isEditable: true,
      }),
    );
    afterEach(() => cleanupScriptTags());

    it("handles a user adding a new reference", async () => {
      const user = userEvent.setup();
      mockPostRequest([{ text: "BBC", url: "https://www.bbc.com" }]);
      render(<References />, { wrapper });

      await waitFor(() => {
        expect(
          screen.getByRole("button", { name: "Add another reference" }),
        ).toBeInTheDocument();
      });

      await user.click(
        screen.getByRole("button", { name: "Add another reference" }),
      );
      expect(screen.getByRole("textbox", { name: "Text" })).toBeVisible();
      expect(screen.getByRole("textbox", { name: "URL" })).toBeVisible();

      await user.type(screen.getByRole("textbox", { name: "Text" }), "BBC");
      await user.type(
        screen.getByRole("textbox", { name: "URL" }),
        "https://www.bbc.com",
      );

      await user.click(screen.getByRole("button", { name: "Save" }));

      await waitFor(() => {
        expect(
          screen.queryByRole("textbox", { name: "Text" }),
        ).not.toBeInTheDocument();
        expect(screen.getByRole("link", { name: "BBC" })).toBeInTheDocument();
        expect(screen.getByRole("link", { name: "BBC" })).toHaveAttribute(
          "href",
          "https://www.bbc.com",
        );
      });
    });

    it("handles a user editing a reference", async () => {
      const user = userEvent.setup();
      mockPostRequest([{ text: "BBC", url: "https://www.bbc.com" }]);
      render(<References />, { wrapper });

      await waitFor(() => {
        expect(
          screen.getByRole("button", { name: "Edit" }),
        ).toBeInTheDocument();
      });

      await user.click(screen.getByRole("button", { name: "Edit" }));
      expect(screen.getByRole("textbox", { name: "Text" })).toBeVisible();
      expect(screen.getByRole("textbox", { name: "URL" })).toBeVisible();
      expect(screen.getByRole("textbox", { name: "Text" })).toHaveValue(
        "Google",
      );
      expect(screen.getByRole("textbox", { name: "URL" })).toHaveValue(
        "https://www.google.com",
      );

      await user.clear(screen.getByRole("textbox", { name: "Text" }));
      await user.clear(screen.getByRole("textbox", { name: "URL" }));
      await user.type(screen.getByRole("textbox", { name: "Text" }), "BBC");
      await user.type(
        screen.getByRole("textbox", { name: "URL" }),
        "https://www.bbc.com",
      );

      await user.click(screen.getByRole("button", { name: "Save" }));

      await waitFor(() => {
        expect(
          screen.queryByRole("textbox", { name: "Text" }),
        ).not.toBeInTheDocument();
        expect(screen.getByRole("link", { name: "BBC" })).toBeInTheDocument();
        expect(screen.getByRole("link", { name: "BBC" })).toHaveAttribute(
          "href",
          "https://www.bbc.com",
        );
      });
    });

    it("handles editing a reference when multiple references exist", async () => {
      const user = userEvent.setup();

      // Setup multiple references
      cleanupScriptTags();
      scriptTagSetup({
        references: [
          { text: "Google", url: "https://www.google.com" },
          { text: "BBC", url: "https://www.bbc.com" },
          { text: "CNN", url: "https://www.cnn.com" },
        ],
        isEditable: true,
      });

      // Mock response with the edited reference and the others unchanged
      mockPostRequest([
        { text: "BBC", url: "https://www.bbc.com" },
        { text: "CNN", url: "https://www.cnn.com" },
        { text: "Yahoo", url: "https://www.yahoo.com" },
      ]);

      render(<References />, { wrapper });

      await waitFor(() => {
        expect(screen.getAllByRole("button", { name: "Edit" })).toHaveLength(3);
      });

      // Click edit on the first reference (Google)
      const editButtons = screen.getAllByRole("button", { name: "Edit" });
      await user.click(editButtons[0]);

      expect(screen.getByRole("textbox", { name: "Text" })).toHaveValue(
        "Google",
      );
      expect(screen.getByRole("textbox", { name: "URL" })).toHaveValue(
        "https://www.google.com",
      );

      // Edit the first reference to Yahoo
      await user.clear(screen.getByRole("textbox", { name: "Text" }));
      await user.clear(screen.getByRole("textbox", { name: "URL" }));
      await user.type(screen.getByRole("textbox", { name: "Text" }), "Yahoo");
      await user.type(
        screen.getByRole("textbox", { name: "URL" }),
        "https://www.yahoo.com",
      );

      await user.click(screen.getByRole("button", { name: "Save" }));

      await waitFor(() => {
        expect(
          screen.queryByRole("textbox", { name: "Text" }),
        ).not.toBeInTheDocument();
        expect(screen.getByRole("link", { name: "Yahoo" })).toBeInTheDocument();
        expect(screen.getByRole("link", { name: "BBC" })).toBeInTheDocument();
        expect(screen.getByRole("link", { name: "CNN" })).toBeInTheDocument();
        expect(
          screen.queryByRole("link", { name: "Google" }),
        ).not.toBeInTheDocument();
      });
    });
  });
});

describe("Delete references", () => {
  beforeEach(() =>
    scriptTagSetup({
      references: [
        { text: "Google", url: "https://www.google.com" },
        { text: "BBC", url: "https://www.bbc.com" },
      ],
      isEditable: true,
    }),
  );
  afterEach(() => cleanupScriptTags());

  it("only deletes the reference with matching URL and text", async () => {
    const user = userEvent.setup();

    mockPostRequest([{ text: "BBC", url: "https://www.bbc.com" }]);

    render(<References />, { wrapper });

    const deleteButtons = screen.getAllByRole("button", { name: "Delete" });
    await user.click(deleteButtons[0]);

    await waitFor(() => {
      expect(
        screen.queryByRole("link", { name: "Google" }),
      ).not.toBeInTheDocument();
      expect(screen.getByRole("link", { name: "BBC" })).toBeInTheDocument();
    });
  });
});
