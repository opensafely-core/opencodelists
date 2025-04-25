import React from "react";
import Item, { ItemProps } from "./Item";

interface SectionProps {
  section: {
    children: ItemProps[]
    title: string;
  }
  slug: string;
  title: string;
}

export default function Section({ section, slug, title }: SectionProps) {
  return (
    <section aria-labelledby={`tree-${slug}`} key={slug} className="tree">
      <h3 className="tree__title" id={`tree-${slug}`}>
        {title}
      </h3>
      <ul
        className="tree__list tree__list--root"
        title={`Codes within the ${title} section`}
      >
        <Item data={section.children} />
      </ul>
    </section>
  );
}
