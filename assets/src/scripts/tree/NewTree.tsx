import slugify from "@sindresorhus/slugify";
import React from "react";
import { Badge } from "react-bootstrap";
import { readValueFromPage } from "../_utils";

function Metadata({ code }: { code: OutputData }) {
  return (
    <dl>
      <dt className="sr-only">Status:</dt>
      <dd>
        {code.status === "+" ? (
          <Badge pill variant="primary">
            Included
          </Badge>
        ) : (
          <Badge pill variant="danger">
            Excluded
          </Badge>
        )}
      </dd>
      <dt className="sr-only">Name:</dt>
      <dd>{code.name}</dd>
      <dt className="sr-only">Code:</dt>
      <dd>{code.id}</dd>
    </dl>
  );
}

function Section({
  section,
}: { section: { title: string; codes: OutputData[] } }) {
  return (
    <section>
      <h3>{section.title}</h3>
      {section.codes.map((code) => (
        <ListItem key={code.id} codeObj={code} />
      ))}
    </section>
  );
}

function ListItem({ codeObj }: { codeObj: OutputData }) {
  const hasChildren = !!codeObj.codes.length;

  return (
    <li>
      {hasChildren ? (
        <details open>
          <summary>
            <Metadata code={codeObj} />
          </summary>
          <ul>
            {codeObj.codes.map((child) => (
              <ListItem key={child.id} codeObj={child} />
            ))}
          </ul>
        </details>
      ) : (
        <Metadata code={codeObj} />
      )}
    </li>
  );
}

interface OutputData {
  id: string;
  name: string;
  status: "+" | "(+)" | "-" | "(-)" | "!" | "?";
  codes: OutputData[];
}

export default function NewTree() {
  const childMap: { string: string[] } = readValueFromPage("child-map");
  const treeTables: [string, string[]][] = readValueFromPage("tree-tables");
  const codeToTerm: { [key: string]: string } =
    readValueFromPage("code-to-term");
  const codeToStatus: { [key: string]: "+" | "(+)" | "-" | "(-)" | "!" | "?" } =
    readValueFromPage("code-to-status");

  function buildTreeData() {
    function processNode(code: string): OutputData {
      const codes = childMap[code as keyof typeof childMap] || [];
      const processedCodes = codes.map((childCode) => processNode(childCode));
      // Sort the processed codes by name
      processedCodes.sort((a, b) => a.name.localeCompare(b.name));

      return {
        id: code,
        name: codeToTerm[code],
        status: codeToStatus[code],
        codes: processedCodes,
      };
    }

    function generateOutputData() {
      return treeTables.map(([title, codes]) => ({
        title,
        codes: codes.map((code) => processNode(code)),
      }));
    }

    return generateOutputData();
  }

  return (
    <div id="test-tree-only">
      {buildTreeData().map((section) => (
        <Section key={slugify(section.title)} section={section} />
      ))}
    </div>
  );
}
