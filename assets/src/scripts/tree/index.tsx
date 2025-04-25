import React, { StrictMode } from "react";
import { createRoot } from "react-dom/client";
import Container from "./Container";

const container = document.getElementById("tree-data");
if (container) {
  const root = createRoot(container);
  root.render(
    <StrictMode>
      <Container />
    </StrictMode>,
  );
}
