import "@testing-library/jest-dom";
import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import nock from "nock";
import React from "react";
import { afterEach, beforeEach, describe, expect, it } from "vitest";
import Hierarchy from "../../../_hierarchy";
import MoreInfoModal from "../../../components/Codelist/MoreInfoModal";
import type { Status } from "../../../types";
import * as versionWithCompleteSearchesData from "../../fixtures/version_with_complete_searches.json";
import { cleanupScriptTags, setScript } from "../../utils";

describe("More info modal", () => {
  beforeEach(() => {
    setScript("builder-config", versionWithCompleteSearchesData.builder_config);
  });

  afterEach(() => {
    cleanupScriptTags(["builder-config"]);
  });

  const props = {
    allCodes: ["123", "456"],
    code: "123",
    codeToStatus: { "123": "+" as Status, "456": "-" as Status },
    codeToTerm: { "123": "Test Term", "456": "Other Term" },
    hierarchy: new Hierarchy(
      versionWithCompleteSearchesData.parent_map,
      versionWithCompleteSearchesData.child_map,
    ),
    status: "+" as Status,
    term: "Test Term",
  };

  it("renders More info button", () => {
    render(<MoreInfoModal {...props} />);
    expect(screen.getByRole("button", { name: /more info/i })).toBeVisible();
  });

  it("shows modal and fetches synonyms and references on button click", async () => {
    const user = userEvent.setup();
    nock("http://localhost:3000/coding-systems/more-info")
      .post("/snomedct")
      .reply(200, {
        synonyms: { "123": ["Alpha", "Beta", "Test Term"] },
        references: { "123": [["TestReference", "https://example.com"]] },
      });
    render(<MoreInfoModal {...props} />);
    await user.click(screen.getByRole("button", { name: /more info/i }));

    await waitFor(() => {
      expect(screen.getByRole("heading", { name: /synonyms/i })).toBeVisible();
      expect(screen.getByText("Alpha")).toBeVisible();
      expect(screen.getByText("Beta")).toBeVisible();
    });

    // Although "Test Term" is returned as a synonym, it shouldn't display as
    // it matches the main term
    expect(screen.queryByText("Test Term")).not.toBeInTheDocument();

    await waitFor(() => {
      expect(
        screen.getByRole("heading", {
          name: /references/i,
        }),
      ).toBeVisible();
      expect(screen.getByText("TestReference")).toBeVisible();
      expect(screen.getByText("TestReference")).toHaveAttribute(
        "href",
        "https://example.com",
      );
    });

    expect(screen.getByText("Included")).toBeVisible();
  });

  it("shows 'No synonyms' if synonyms is empty", async () => {
    const user = userEvent.setup();
    nock("http://localhost:3000/coding-systems/more-info")
      .post("/snomedct")
      .reply(200, {
        synonyms: {},
        references: {},
      });
    render(<MoreInfoModal {...props} code="456" />);
    await user.click(screen.getByRole("button", { name: /more info/i }));
    await waitFor(() => {
      expect(screen.getByText(/no synonyms/i)).toBeVisible();
    });
  });

  it("shows 'No synonyms' if fetch fails", async () => {
    const user = userEvent.setup();
    render(<MoreInfoModal {...props} />);

    await user.click(screen.getByRole("button", { name: /more info/i }));
    expect(await screen.findByText(/no synonyms/i)).toBeVisible();
  });

  it("shows 'No synonyms' if fetch succeeds but has an error message", async () => {
    nock("http://localhost:3000/coding-systems/more-info")
      .post("/snomedct")
      .replyWithError("Err");
    const user = userEvent.setup();
    render(<MoreInfoModal {...props} />);

    await user.click(screen.getByRole("button", { name: /more info/i }));
    expect(await screen.findByText(/no synonyms/i)).toBeVisible();
  });

  it("show 'No synonyms' if the only synonym matches the primary term", async () => {
    nock("http://localhost:3000/coding-systems/more-info")
      .post("/snomedct")
      .reply(200, {
        synonyms: { "123": ["Test Term"] },
      });
    const user = userEvent.setup();
    render(<MoreInfoModal {...props} />);
    await user.click(screen.getByRole("button", { name: /more info/i }));
    expect(await screen.findByText(/no synonyms/i)).toBeVisible();
  });
});
