import htm from "htm";
import vhtml from "vhtml";

const html = htm.bind(vhtml);

const renderTree = (tree) => {
  const { code, term, status, pipes, expandable, expanded, children } = tree;

  return html`<div
    class="tree-node mt-0"
    data-code=${code}
    data-status=${status}
    data-expanded=${expanded}
  >
    <div class="tree-item d-flex">
      <div class="tree-buttons btn-group btn-group-sm" role="group">
        ${renderStatusToggle("+")} ${renderStatusToggle("-")}
      </div>

      <div class="tree-pipes pl-2 d-flex">
        ${pipes.map((pipe) => renderPipe(pipe))}
      </div>

      ${expandable && renderVisibilityToggle(expanded)}

      <div class="tree-term-and-code">
        <span class="tree-term">${term}</span>
        <span class="tree-code ml-1"> (<code>${code}</code>)</span>
      </div>
    </div>

    <div class="tree-children">
      ${children.map((child) => renderTree(child))}
    </div>
  </div>`;
};

const renderStatusToggle = (symbol) => {
  return html`<button
    type="button"
    class="tree-status-toggle btn py-0"
    data-symbol=${symbol}
  >
    ${symbol}
  </button>`;
};

const renderVisibilityToggle = (expanded) => {
  return html`<div class="tree-visibility-toggle">
    ${expanded ? "⊟" : "⊞"}
  </div>`;
};

const renderPipe = (pipe) => {
  return html`<span class="tree-pipe">${pipe}</span>`;
};

export { renderTree as default };
