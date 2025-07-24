import slugify from "@sindresorhus/slugify";
import React from "react";
import { readValueFromPage } from "../_utils";
import type { CodeProps } from "./ListGroup";
import Section from "./Section";

interface SectionProps {
  children: CodeProps[];
  title: string;
}

export default function Container() {
  const treeData = readValueFromPage("tree_data");

  return (
    <>
      {treeData.map((section: SectionProps) => (
        <Section
          key={`section-${slugify(section.title)}`}
          section={section}
          slug={slugify(section.title)}
          title={section.title}
        />
      ))}
    </>
  );
}
