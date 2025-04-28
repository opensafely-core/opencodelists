import React from "react";
import { Badge } from "react-bootstrap";

export default function Title({ name }: { name: string }) {
  return (
    <div className="border-bottom mb-3">
      <h1 className="h3">
        {name}
        <Badge className="align-text-bottom ml-1" variant="secondary">
          Draft
        </Badge>
      </h1>
    </div>
  );
}
