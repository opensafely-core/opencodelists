import React, { useState } from "react";
import { readValueFromPage } from "../../_utils";
import listOfTools from "../../data/tools.json";
import { METADATA } from "../../types";

export default function Tools() {
  const codingSystemId: METADATA["coding_system_id"] =
    readValueFromPage("metadata")?.coding_system_id;

  if (!codingSystemId) return null;

  const [tools] = useState(() => {
    return listOfTools.filter((tool) =>
      tool.codingSystem.includes(codingSystemId),
    );
  });

  if (!tools.length) return null;

  return (
    <div className="card">
      <div className="card-header">
        <h2 className="h6 font-weight-bold mb-1">Tools</h2>
        <p className="small mb-0">
          Tools to help you to build a better and more accurate codelist.
        </p>
      </div>
      <ul className="list-group list-group-flush">
        {tools.map((tool) => (
          <li key={tool.id} className="list-group-item">
            <a
              href={tool.link}
              target="_blank"
              rel="noopener noreferrer"
              className={`plausible-event-name=Builder+tool+click plausible-event-tool=${tool.id}`}
            >
              {tool.name}
            </a>
            {tool?.description && (
              <p className="small mb-0">{tool.description}</p>
            )}
          </li>
        ))}
      </ul>
    </div>
  );
}
