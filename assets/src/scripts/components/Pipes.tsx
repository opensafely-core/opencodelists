import React from "react";
import { PipesState } from "../types";

interface PipesProps {
  pipes: PipesState;
}

export default function Pipes({ pipes }: PipesProps) {
  return pipes.map((pipe, ix) => (
    <span
      key={ix}
      className="d-inline-block pl-1 pr-2 text-center text-monospace"
    >
      {pipe}
    </span>
  ));
}
