// Shared TypeScript types for LP Solver

export interface Constraint {
  coeffs: (number | "")[];
  type: "<=" | ">=" | "=";
  rhs: number | "";
}

export interface SolveRequest {
  method: "standard" | "bland" | "two-phase";
  objective: "max" | "min";
  c: number[];
  constraints: { coeffs: number[]; type: string; rhs: number }[];
  bounds: ([number, null] | [number, number])[];
  show_steps: boolean;
}

export interface TableauStep {
  phase?: number;
  note: string;
  basic_vars?: string[];
  rows?: string[][];
  pivot_col?: number | null;
  pivot_row?: number | null;
  dictionary_str?: string;
  point_str?: string;
}

export interface SolveResult {
  status: "optimal" | "multiple" | "infeasible" | "unbounded" | "cycling" | "method_error";
  message: string;
  optimal_value: string | null;
  solution: Record<string, string>;
  steps: TableauStep[];
  // Extra data attached on frontend for chart
  c?: number[];
  constraints?: { coeffs: number[]; type: string; rhs: number }[];
  graph_data?: {
    vertices: { name: string; x1: number; x2: number; intersect_of?: number[] }[];
    constraints: { a: number; b: number; type: string; rhs: number; is_bound: boolean }[];
    objective_line: { c1: number; c2: number; lcm: number; objective: string };
    bounding_box: { x_min: number; x_max: number; y_min: number; y_max: number };
    simplex_path?: { name: string; x1: number; x2: number }[];
  };
}
