import React from "react";

type PipeType = "└" | "├" | " " | "│";

interface PipesProps {
  pipes: PipeType[];
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
