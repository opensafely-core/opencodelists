import React, { StrictMode } from "react";
import { createRoot } from "react-dom/client";
import NewTree from "./NewTree";

const container = document.getElementById("codelist-tree");
if (container) {
  const root = createRoot(container);
  root.render(
    <StrictMode>
      <NewTree />
    </StrictMode>,
  );
}
