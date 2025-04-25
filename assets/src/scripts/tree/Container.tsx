import slugify from "@sindresorhus/slugify";
import React from "react";
import { readValueFromPage } from "../_utils";
import { ItemProps } from "./Item";
import Section from "./Section";

interface SectionProps {
  children: ItemProps[];
  title: string;
}

export default function Container() {
  const treeData = readValueFromPage("tree_data");

  return (
    <>
      {treeData.map((section: SectionProps) => (
        <Section
          key={slugify(section.title)}
          section={section}
          slug={slugify(section.title)}
          title={section.title}
        />
      ))}
    </>
  );
}
