type PipeState = "└" | "├" | " " | "│";
export type PipesState = PipeState[];

export type StatusState = "+" | "(+)" | "-" | "(-)" | "!" | "?";

export interface CodeToStatus {
  [key: string]: StatusState;
}
