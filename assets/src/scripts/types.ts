import Hierarchy from "./_hierarchy";

export type AllCodesType = string[];

type PipeState = "└" | "├" | " " | "│";
export type PipesState = PipeState[];

export type StatusState = "+" | "(+)" | "-" | "(-)" | "!" | "?";

export interface CodeToStatus {
  [key: string]: StatusState;
}

export type AncestorCodeType = string;

export interface TreePassProps {
  allCodes: AllCodesType;
  codeToStatus: CodeToStatus;
  codeToTerm: {
    [key: string]: string;
  };
  hierarchy: Hierarchy;
  isEditable: boolean;
  toggleVisibility: (path: string) => void;
  updateStatus: Function;
  visiblePaths: Set<string>;
}
