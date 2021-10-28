console.log("builder2");
import htm from "htm";
import vhtml from "vhtml";

import { readValueFromPage } from "./utils";
import Hierarchy from "./hierarchy";

const html = htm.bind(vhtml);

const codeToTerm = readValueFromPage("code-to-term");
const codeToStatus = readValueFromPage("code-to-status");
const hierarchy = new Hierarchy(
  readValueFromPage("parent-map"),
  readValueFromPage("child-map")
);

document.addEventListener("click", (event) => {
  event.target.matches(".tree-visibility-toggle") &&
    toggleVisibility(event.target);
});

const toggleVisibility = (visibilityToggle) => {
  event.preventDefault();
  const node = visibilityToggle.closest(".tree-node");
  const children = node.querySelector(".tree-children");

  if (node.hasAttribute("data-expanded")) {
    // node is expanded, so collapse it
    node.removeAttribute("data-expanded");
    visibilityToggle.innerHTML = "⊞";
    children.setAttribute("hidden", "");
  } else {
    // node is collapsed, so expand it
    node.setAttribute("data-expanded", "");
    visibilityToggle.innerHTML = "⊟";
    if (children === null) {
      addChildren(node);
    } else {
      children.removeAttribute("hidden");
    }
  }
};

const addChildren = (node) => {
  const code = node.dataset["code"];
  const childCodes = hierarchy.childMap[code];

  childCodes.sort((code1, code2) => {
    const term1 = codeToTerm[code1];
    const term2 = codeToTerm[code2];
    if (term1 < term2) {
      return -1;
    } else if (term2 < term1) {
      return 1;
    } else {
      return 0;
    }
  });

  node.querySelector(".tree-children-go-here").outerHTML = html`<div
    class="tree-children"
  >
    ${childCodes.map((childCode, ix) =>
      childNode(
        childCode,
        codeToTerm[childCode],
        codeToStatus[childCode],
        ix === childCodes.length - 1
      )
    )}
  </div>`;
};

const childNode = (code, term, status, isLastSibling) => {
  console.log(code, term, isLastSibling);
  return html`<div data-code="${code}" class="tree-node mt-0">
    <div class="tree-item d-flex">
      <div class="tree-buttons btn-group btn-group-sm" role="group">
        ${includeExcludeButton("+", status)}
        ${includeExcludeButton("-", status)}
      </div>

      <div class="tree-pipes pl-2"></div>

      <div class="pl-2" style="white-space: nowrap;">
        <span>${term}</span>
        <span class="ml-1"> (<code>${code}</code>)</span>
      </div>
    </div>
  </div>`;
};

const includeExcludeButton = (symbol, status) => {
  let buttonClass =
    status === symbol
      ? "btn-primary"
      : status === `(${symbol})`
      ? "btn-secondary"
      : "btn-outline-secondary";
  buttonClass = `btn ${buttonClass} py-0`;
  return html`<button type="button" class=${buttonClass}>${symbol}</button>`;
};
