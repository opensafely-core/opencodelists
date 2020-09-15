"use strict";

import ReactDOM from "react-dom";
// Although React is not used in this module, if this line is removed, there is
// a runtime error in codelistbuilder.jsx.
import React from "react";

import Hierarchy from "../hierarchy";
import Tree from "./Tree";
import { readValueFromPage } from "../utils";

const hierarchy = new Hierarchy(
  readValueFromPage("parent-map"),
  readValueFromPage("child-map")
);

ReactDOM.render(
  <Tree hierarchy={hierarchy} trees={readValueFromPage("trees")} />,
  document.querySelector("#codelist-tree")
);
