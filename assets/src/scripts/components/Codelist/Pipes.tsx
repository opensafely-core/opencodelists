import React from "react";
import type { Pipe } from "../../types";

interface PipesProps {
  pipes: Pipe[];
}

export default function Pipes({ pipes }: PipesProps) {
  return pipes.map((pipe, ix) => (
    <span
      // biome-ignore lint/suspicious/noArrayIndexKey: legacy pipes for UI
      key={ix}
      className="d-inline-block pl-1 pr-2 text-center text-monospace"
    >
      {pipe}
    </span>
  ));
}
