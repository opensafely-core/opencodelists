import { expect, it } from "vitest";
import { getCookie, readValueFromPage } from "../_utils";

it("gets the cookie value", () => {
  const name = "csrftoken";
  const value = "01JJ6V33G19M1ZFEB4JAQMMTQW";
  // biome-ignore lint/suspicious/noDocumentCookie: only used in tests
  document.cookie = `${name}=${value || ""};`;
  expect(getCookie(name)).toBe(value);
});

it("reads the values of a JSON script on the page", () => {
  const blob = {
    hello: "world",
  };
  document.body.innerHTML = `
    <script id="all-codes">${JSON.stringify(blob)}</script>
  `;

  expect(readValueFromPage("all-codes")).toEqual(blob);
});
