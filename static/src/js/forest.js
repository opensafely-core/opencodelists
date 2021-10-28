// A Forest is a collection of trees...

import Hierarchy from "./hierarchy";
import renderTree from "./render";
import { readValueFromPage } from "./utils";

class Forest {
  constructor(codeToTerm, codeToStatus, hierarchy) {
    this.codeToTerm = codeToTerm;
    this.codeToStatus = codeToStatus;
    this.hierarchy = hierarchy;
  }

  set_up(roots, saveButton, summary, codeToStatusInput) {
    // ...
    console.log(codeToStatusInput);
    roots.forEach((root) => {
      const code = root.dataset["code"];
      const tree = this.buildTree(code, 2, null, null, null);
      root.innerHTML = renderTree(tree);
    });
    this.saveButton = saveButton;
    this.summary = summary;
    this.codeToStatusInput = codeToStatusInput;
    this.updateRestOfDom();
  }

  addChildren(node) {
    const children = node.querySelector(".tree-children");
    const code = node.dataset["code"];
    const childCodes = this.hierarchy.childMap[code];
    const pipes = Array.from(node.querySelectorAll(".tree-pipe")).map(
      (pipeEl) => pipeEl.innerHTML
    );
    const isLastSibling = pipes[pipes.length - 1] === "└";

    childCodes.forEach((childCode, ix) => {
      const childIsLastSibling = ix === childCodes.length - 1;
      const tree = this.buildTree(
        childCode,
        1,
        childIsLastSibling,
        isLastSibling,
        pipes,
        this
      );
      children.innerHTML += renderTree(tree);
    });
  }

  buildTree(code, depth, isLastSibling, parentIsLastSibling, parentPipes) {
    const childCodes = this.hierarchy.childMap[code] || [];

    // Sort childCodes by corresponding term
    childCodes.sort((code1, code2) => {
      const term1 = this.codeToTerm[code1];
      const term2 = this.codeToTerm[code2];
      if (term1 < term2) {
        return -1;
      } else if (term2 < term1) {
        return 1;
      } else {
        return 0;
      }
    });

    const newDepth = this.hierarchy.allDescendantsHaveSameStatus(
      code,
      this.codeToStatus
    )
      ? depth - 1
      : depth;

    // Pipes are used to show the relationship between nodes in the tree.  A node at depth
    // N has N pipes, with the root being at depth 0.  A node's pipes are determined by:
    //
    //  (a) the node's parent's pipes
    //  (b) whether the node's parent is the last of its siblings
    //  (c) whether the node itself is the last of its siblings
    //
    // Consider the following tree, with the array of pipes for each node in the RH column:
    //
    // A                  []
    // ├ B                ["├"]
    // │ ├ D              ["│", "├"]
    // │ │ ├ H            ["│", "│", "├"]
    // │ │ └ I            ["│", "│", "└"]
    // │ └ E              ["│", "└"]
    // │   ├ J            ["│", " ", "├"]
    // │   └ K            ["│", " ", "└"]
    // └ C                ["└"]
    //   ├ F              [" ", "├"]
    //   │ ├ L            [" ", "│", "├"]
    //   │ └ M            [" ", "│", "└"]
    //   └ G              [" ", "└"]
    //     ├ N            [" ", " ", "├"]
    //     └ O            [" ", " ", "└"]
    //
    //  There are three cases to consider:
    //
    //  (1) A node at depth 0 (ie the root)
    //      * It has no pipes
    //  (2) A node at depth 1 (ie a child of the root)
    //      * It has a single pipe, which is determined by whether it is the last of its
    //        siblings.
    //  (3) A node at depth N (with N > 1)
    //      * Its last pipe is determined by whether it is the last of its siblings
    //      * Its penultimate pipe is determined by whether its parent is the last of its
    //        siblings
    //      * The other pipes are all but the last of the parent's pipes
    let pipes;
    if (parentPipes === null) {
      // This is the root of the tree
      pipes = [];
    } else if (parentPipes.length === 0) {
      // This is a child of the root of the tree
      pipes = [isLastSibling ? "└" : "├"];
    } else {
      pipes = parentPipes
        .slice(0, -1)
        .concat(parentIsLastSibling ? " " : "│")
        .concat(isLastSibling ? "└" : "├");
    }

    const children =
      depth === 1
        ? []
        : childCodes.map((childCode, ix) =>
            this.buildTree(
              childCode,
              newDepth,
              ix === childCodes.length - 1,
              isLastSibling,
              pipes,
              this
            )
          );

    return {
      code: code,
      term: this.codeToTerm[code],
      status: this.codeToStatus[code],
      pipes: pipes,
      expandable: childCodes.length > 0,
      expanded: childCodes.length > 0 && children.length > 0,
      children: children,
    };
  }

  toggleVisibility(visibilityToggle) {
    const node = visibilityToggle.closest(".tree-node");
    const children = node.querySelector(".tree-children");

    if (node.hasAttribute("data-expanded")) {
      node.removeAttribute("data-expanded");
      children.setAttribute("hidden", "");
      visibilityToggle.innerHTML = "⊞";
    } else {
      if (children.childElementCount === 0) {
        this.addChildren(node);
      }
      node.setAttribute("data-expanded", "");
      children.removeAttribute("hidden");
      visibilityToggle.innerHTML = "⊟";
    }
  }

  toggleStatus(statusToggle) {
    const node = statusToggle.closest(".tree-node");
    const code = node.dataset["code"];
    const symbol = statusToggle.dataset["symbol"];

    // Update the mapping from code to status.
    this.codeToStatus = this.hierarchy.updateCodeToStatus(
      this.codeToStatus,
      code,
      symbol
    );

    // Update the data-status attributes in the DOM.
    const root = node.closest(".tree-root");
    root.querySelectorAll(".tree-node").forEach((node) => {
      const code = node.dataset["code"];
      if (node.dataset["status"] !== this.codeToStatus[code]) {
        node.dataset["status"] = this.codeToStatus[code];
      }
    });

    // Update other dynamic elements in the DOM.
    this.updateRestOfDom();
  }

  updateRestOfDom() {
    //
    const countsByStatus = this.countsByStatus();
    this.updateSummary(countsByStatus);
    this.updateSaveButton(countsByStatus);
    this.updateCodeToStatusInput();
  }

  updateSummary(countsByStatus) {
    const lines = [];

    lines.push(
      `<p>Found ${countsByStatus.total} matching concepts (including descendants).</p>`
    );
    if (countsByStatus["+"] > 0) {
      const num = countsByStatus["+"] + countsByStatus["(+)"];
      lines.push(`<p>${num} have been included in the codelist.</p>`);
    }
    if (countsByStatus["-"] > 0) {
      const num = countsByStatus["-"] + countsByStatus["(-)"];
      lines.push(`<p>${num} have been excluded from the codelist.</p>`);
    }
    if (countsByStatus["?"] > 0) {
      lines.push(`<p>${countsByStatus["?"]} are unresolved.</p>`);
    }
    if (countsByStatus["!"] > 0) {
      lines.push(`<p>${countsByStatus["!"]} are in conflict.</p>`);
    }

    this.summary.innerHTML = lines.join("");
  }

  updateSaveButton(countsByStatus) {
    if (countsByStatus["!"] > 0 || countsByStatus["?"] > 0) {
      // The draft cannot be saved for review, since some codes are either in conflict
      // or are unresolved.
      this.saveButton.setAttribute("type", "button");
      this.saveButton.setAttribute("aria-disabled", "");
      this.saveButton.setAttribute("data-toggle", "tooltip");
      this.saveButton.setAttribute(
        "title",
        "You cannot save for review until all search results are included or excluded"
      );
      this.saveButton.classList.add("btn-outline-secondary", "disabled");
      this.saveButton.classList.remove("btn-outline-primary");
    } else {
      // The draft can be saved for review, since all codes are either included or
      // excluded.
      this.saveButton.setAttribute("type", "submit");
      this.saveButton.removeAttribute("aria-disabled");
      this.saveButton.removeAttribute("data-toggle");
      this.saveButton.removeAttribute("title");
      this.saveButton.classList.add("btn-outline-primary");
      this.saveButton.classList.remove("btn-outline-secondary", "disabled");
    }
  }

  updateCodeToStatusInput() {
    this.codeToStatusInput.value = JSON.stringify(this.codeToStatus);
  }

  countsByStatus() {
    let countsByStatus = {
      "?": 0,
      "!": 0,
      "+": 0,
      "(+)": 0,
      "-": 0,
      "(-)": 0,
      total: 0,
    };
    Object.values(this.codeToStatus).forEach((status) => {
      countsByStatus[status] += 1;
      countsByStatus["total"] += 1;
    });
    return countsByStatus;
  }
}

const forest = new Forest(
  readValueFromPage("code-to-term"),
  readValueFromPage("code-to-status"),
  new Hierarchy(readValueFromPage("parent-map"), readValueFromPage("child-map"))
);

document.addEventListener("click", (event) => {
  if (event.target.matches(".tree-visibility-toggle")) {
    event.preventDefault();
    forest.toggleVisibility(event.target);
  }

  if (event.target.matches(".tree-status-toggle")) {
    event.preventDefault();
    forest.toggleStatus(event.target);
  }
});

document.addEventListener("DOMContentLoaded", () => {
  forest.set_up(
    document.querySelectorAll(".tree-root"),
    document.querySelector("#save-button"),
    document.querySelector("#summary"),
    document.querySelector("input[name='definition']")
  );
});
