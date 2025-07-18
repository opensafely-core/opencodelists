import React from "react";
import { Pipe } from "../../types";

interface PipesProps {
  pipes: Pipe[];
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
