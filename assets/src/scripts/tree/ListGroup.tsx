import slugify from "@sindresorhus/slugify";
import React from "react";

export interface CodeProps {
  id: string;
  name: string;
  status: "+" | "-";
  children: CodeProps[];
  depth: number;
}

function Status({ status }: { status: "+" | "-" }) {
  const isIncluded = status === "+";

  return (
    <>
      <dt className="sr-only">Status:</dt>
      <dd
        className={`tree__dd tree__badge ${isIncluded ? "tree__badge--included" : "tree__badge--excluded"}`}
      >
        {isIncluded ? "Included" : "Excluded"}
      </dd>
    </>
  );
}

function Codename({
  name,
  status,
}: {
  name: CodeProps["name"];
  status: CodeProps["status"];
}) {
  return (
    <>
      <dt className="sr-only">Name:</dt>
      <dd
        className={`tree__dd tree__name ${status === "-" && "tree__name--excluded"}`}
      >
        {name}
      </dd>
    </>
  );
}

function ID({ id }: { id: string }) {
  return (
    <>
      <dt className="sr-only">Code:</dt>
      <dd className="tree__dd">
        (<code>{id}</code>)
      </dd>
    </>
  );
}

function Item({ className, code }: { className?: string; code: CodeProps }) {
  return (
    <dl className={`tree__dl ${className}`}>
      <Status status={code.status} />
      <Codename name={code.name} status={code.status} />
      <ID id={code.id} />
    </dl>
  );
}

function ArrowIcon() {
  return (
    <svg
      className="tree__arrow"
      fill="currentColor"
      height="20"
      viewBox="0 0 20 20"
      width="20"
      xmlns="http://www.w3.org/2000/svg"
    >
      <path
        clipRule="evenodd"
        d="M8.22 5.22a.75.75 0 0 1 1.06 0l4.25 4.25a.75.75 0 0 1 0 1.06l-4.25 4.25a.75.75 0 0 1-1.06-1.06L11.94 10 8.22 6.28a.75.75 0 0 1 0-1.06Z"
        fillRule="evenodd"
      />
    </svg>
  );
}

function Dropdown({ code }: { code: CodeProps }) {
  return (
    <details className="tree__details" open={code.depth < 2}>
      <summary className="tree__summary">
        <ArrowIcon />
        <Item
          className="tree__dl--dropdown"
          code={code}
          key={`item-${slugify(code.id)}`}
        />
      </summary>
      <ul className="tree__list">
        <ListGroup data={code.children} key={`list-${code.id}`} />
      </ul>
    </details>
  );
}

export default function ListGroup({ data }: { data: CodeProps[] }) {
  return (
    <>
      {data.map((code) => (
        <li className="tree__item" key={code.id} title={code.name}>
          {code.children.length ? (
            <Dropdown code={code} key={`dropdown-${slugify(code.id)}`} />
          ) : (
            <Item code={code} key={`item-${slugify(code.id)}`} />
          )}
        </li>
      ))}
    </>
  );
}
