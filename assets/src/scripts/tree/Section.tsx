import React from "react";
import ListGroup, { type CodeProps } from "./ListGroup";

interface SectionProps {
  section: {
    children: CodeProps[];
    title: string;
  };
  slug: string;
  title: string;
}

export default function Section({ section, slug, title }: SectionProps) {
  return (
    <section aria-labelledby={`tree-${slug}`} className="tree">
      <h3 className="tree__title" id={`tree-${slug}`}>
        {title}
      </h3>
      <ul
        className="tree__list tree__list--root"
        title={`Codes within the ${title} section`}
      >
        <ListGroup data={section.children} key={`list-${slug}`} />
      </ul>
    </section>
  );
}
