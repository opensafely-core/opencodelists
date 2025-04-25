import React from "react";

export interface ItemProps {
  id: string;
  name: string;
  status: "+" | "-";
  children: ItemProps[];
  depth: number;
}

export default function Item({ data }: { data: ItemProps[] }) {
  return (
    <>
      {data.map((code) => (
        <li className="tree__item" key={code.id} title={code.name}>
          {code.children.length ? (
            <details className="tree__details" open={code.depth < 2}>
              <summary className="tree__summary">
                <svg
                  className="tree__arrow"
                  width="20"
                  height="20"
                  xmlns="http://www.w3.org/2000/svg"
                  viewBox="0 0 20 20"
                  fill="currentColor"
                >
                  <path
                    fill-rule="evenodd"
                    d="M8.22 5.22a.75.75 0 0 1 1.06 0l4.25 4.25a.75.75 0 0 1 0 1.06l-4.25 4.25a.75.75 0 0 1-1.06-1.06L11.94 10 8.22 6.28a.75.75 0 0 1 0-1.06Z"
                    clip-rule="evenodd"
                  />
                </svg>
                <dl className="tree__dl tree__dl--dropdown">
                  <dt className="sr-only">Status:</dt>
                  <dd
                    className={`tree__dd tree__badge ${code.status === "+" ? "tree__badge--included" : "tree__badge--excluded"}`}
                  >
                    {code.status === "+" ? "Included" : "Excluded"}
                  </dd>
                  <dt className="sr-only">Name:</dt>
                  <dd
                    className={`tree__dd tree__name ${code.status === "-" && "tree__name--excluded"}`}
                  >
                    {code.name}
                  </dd>
                  <dt className="sr-only">Code:</dt>
                  <dd className="tree__dd">
                    (<code>{code.id}</code>)
                  </dd>
                </dl>
              </summary>
              <ul
                className="tree__list"
                title="Codes within the {{ section.title }} section"
              >
                <Item data={code.children} />
              </ul>
            </details>
          ) : (
            <dl className="tree__dl">
              <dt className="sr-only">Status:</dt>
              <dd
                className={`tree__dd tree__badge ${code.status === "+" ? "tree__badge--included" : "tree__badge--excluded"}`}
              >
                {code.status === "+" ? "Included" : "Excluded"}
              </dd>
              <dt className="sr-only">Name:</dt>
              <dd
                className={`tree__dd tree__name ${code.status === "-" && "tree__name--excluded"}`}
              >
                {code.name}
              </dd>
              <dt className="sr-only">Code:</dt>
              <dd className="tree__dd">
                (<code>{code.id}</code>)
              </dd>
            </dl>
          )}
        </li>
      ))}
    </>
  );
}
