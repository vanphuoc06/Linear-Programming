"use client";
import dynamic from "next/dynamic";
import { SolveResult } from "@/types";

const Plot = dynamic(() => import("react-plotly.js"), { ssr: false });

interface Props { result: SolveResult }

// Parse fraction string like "1/3", "-5", "4" to float
function parseFrac(s: string): number {
  if (s.includes("/")) {
    const [n, d] = s.split("/").map(Number);
    return n / d;
  }
  return Number(s);
}

export default function Chart2D({ result }: Props) {
  if (!result.c || !result.constraints) return null;

  const constraints = result.constraints;
  const c = result.c;

  // Compute optimal point
  const x_opt = parseFrac(result.solution?.["x1"] ?? "0");
  const y_opt = parseFrac(result.solution?.["x2"] ?? "0");

  // Axis range
  const maxRhs = Math.max(...constraints.map((con) => Math.abs(con.rhs)), 10) * 1.3;

  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  const traces: any[] = [];
  const colors = ["#6366f1", "#8b5cf6", "#ec4899", "#f59e0b", "#10b981", "#3b82f6"];

  // Draw constraint lines
  constraints.forEach((con, i) => {
    const [a, b] = con.coeffs;
    const rhs = con.rhs;
    const color = colors[i % colors.length];
    const xs: number[] = [];
    const ys: number[] = [];

    if (Math.abs(b) > 1e-9) {
      // y = (rhs - a*x) / b
      for (let x = 0; x <= maxRhs; x += maxRhs / 100) {
        xs.push(x);
        ys.push((rhs - a * x) / b);
      }
    } else if (Math.abs(a) > 1e-9) {
      // x = rhs / a (vertical line)
      const xv = rhs / a;
      for (let y = 0; y <= maxRhs; y += maxRhs / 100) {
        xs.push(xv);
        ys.push(y);
      }
    }

    traces.push({
      x: xs, y: ys, mode: "lines", name: `C${i + 1}: ${con.coeffs.map((coeff, j) => `${coeff}x${j + 1}`).join(" + ")} ${con.type} ${con.rhs}`,
      line: { color, width: 2 },
      type: "scatter",
    });
  });

  // Shade feasible region via convex hull approximation
  const points: [number, number][] = [];
  const n = constraints.length;

  // Add origin if feasible
  points.push([0, 0]);

  // Axis intercepts
  constraints.forEach((con) => {
    const [a, b] = con.coeffs;
    const rhs = con.rhs;
    if (Math.abs(a) > 1e-9) points.push([rhs / a, 0]);
    if (Math.abs(b) > 1e-9) points.push([0, rhs / b]);
  });

  // Pairwise intersections
  for (let i = 0; i < n; i++) {
    for (let j = i + 1; j < n; j++) {
      const [a1, b1] = constraints[i].coeffs;
      const [a2, b2] = constraints[j].coeffs;
      const det = a1 * b2 - a2 * b1;
      if (Math.abs(det) < 1e-9) continue;
      const x = (constraints[i].rhs * b2 - constraints[j].rhs * b1) / det;
      const y = (a1 * constraints[j].rhs - a2 * constraints[i].rhs) / det;
      if (x >= -1e-6 && y >= -1e-6) points.push([x, y]);
    }
  }

  // Filter points that satisfy ALL constraints
  const feasible = points.filter(([x, y]) =>
    x >= -1e-6 && y >= -1e-6 &&
    constraints.every((con) => {
      const val = con.coeffs[0] * x + con.coeffs[1] * y;
      if (con.type === "<=") return val <= con.rhs + 1e-6;
      if (con.type === ">=") return val >= con.rhs - 1e-6;
      return Math.abs(val - con.rhs) <= 1e-6;
    })
  );

  // Sort by angle for polygon
  if (feasible.length >= 3) {
    const cx = feasible.reduce((s, p) => s + p[0], 0) / feasible.length;
    const cy = feasible.reduce((s, p) => s + p[1], 0) / feasible.length;
    feasible.sort(([ax, ay], [bx, by]) => Math.atan2(ay - cy, ax - cx) - Math.atan2(by - cy, bx - cx));

    traces.push({
      x: [...feasible.map(p => p[0]), feasible[0][0]],
      y: [...feasible.map(p => p[1]), feasible[0][1]],
      fill: "toself",
      fillcolor: "rgba(99,102,241,0.12)",
      line: { color: "rgba(99,102,241,0.5)", width: 1 },
      name: "Miền nghiệm",
      type: "scatter",
      mode: "lines",
    });
  }

  // Objective function direction arrow
  const norm = Math.sqrt(c[0] ** 2 + c[1] ** 2) || 1;
  const arrowScale = maxRhs * 0.15;
  traces.push({
    x: [x_opt, x_opt + c[0] / norm * arrowScale],
    y: [y_opt, y_opt + c[1] / norm * arrowScale],
    mode: "lines+markers",
    name: "Hướng tối ưu",
    line: { color: "#f59e0b", width: 2, dash: "dot" },
    marker: { symbol: "arrow", size: 10, color: "#f59e0b", angleref: "previous" },
    type: "scatter",
  });

  // Optimal point
  traces.push({
    x: [x_opt], y: [y_opt],
    mode: "markers+text",
    name: `Điểm tối ưu (${result.solution?.["x1"]}, ${result.solution?.["x2"]})`,
    marker: { size: 16, color: "#ef4444", symbol: "star", line: { color: "white", width: 2 } },
    text: [`  Z*=${result.optimal_value}`],
    textposition: "top right",
    textfont: { color: "#ef4444", size: 13, family: "JetBrains Mono" },
    type: "scatter",
  });

  // Hiển thị các đỉnh (vertices) với label tọa độ như trong QHTT
  if (result.graph_data?.vertices) {
    const vx = result.graph_data.vertices.map((v) => v.x1);
    const vy = result.graph_data.vertices.map((v) => v.x2);
    // Format "A(0, 8)"
    const vtext = result.graph_data.vertices.map((v) => ` ${v.name}(${Number(v.x1.toFixed(3))}, ${Number(v.x2.toFixed(3))})`);
    
    traces.push({
      x: vx, y: vy,
      mode: "markers+text",
      name: "Các điểm",
      marker: { size: 9, color: "#a78bfa", line: { color: "white", width: 1 } },
      text: vtext,
      textposition: "top right",
      textfont: { color: "#c4b5fd", size: 12, family: "Inter", weight: "bold" },
      type: "scatter",
    });
  }

  // Vẽ các đoạn thẳng có mũi tên nối các điểm theo tiến trình Simplex (Từ vựng)
  if (result.graph_data?.simplex_path) {
    const path = result.graph_data.simplex_path;
    for (let i = 0; i < path.length - 1; i++) {
      const p1 = path[i];
      const p2 = path[i + 1];
      traces.push({
        x: [p1.x1, p2.x1],
        y: [p1.x2, p2.x2],
        mode: "lines+markers",
        name: `Đường đi (Bước ${i + 1})`,
        line: { color: "#34d399", width: 3 },
        marker: { symbol: "arrow", size: 12, color: "#34d399", angleref: "previous" },
        type: "scatter",
      });
    }
  }

  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  const layout: any = {
    paper_bgcolor: "transparent",
    plot_bgcolor: "rgba(17,24,39,0.7)",
    font: { color: "#f9fafb", family: "Inter" },
    xaxis: {
      title: "x₁", gridcolor: "#374151", zerolinecolor: "#6b7280",
      range: [-0.5, maxRhs], color: "#9ca3af",
    },
    yaxis: {
      title: "x₂", gridcolor: "#374151", zerolinecolor: "#6b7280",
      range: [-0.5, maxRhs], color: "#9ca3af",
    },
    legend: { bgcolor: "rgba(17,24,39,0.8)", bordercolor: "#374151", borderwidth: 1, font: { size: 11 } },
    margin: { l: 50, r: 20, t: 20, b: 50 },
    hovermode: "closest",
  };

  return (
    <div className="card" style={{ padding: 0, overflow: "hidden" }}>
      <div style={{ padding: "16px 20px", borderBottom: "1px solid var(--border)" }}>
        <h2 style={{ fontSize: 18, fontWeight: 700 }}>📈 Đồ thị 2D — Miền nghiệm</h2>
        <p style={{ fontSize: 12, color: "var(--text-muted)", marginTop: 4 }}>Vùng tô màu là miền nghiệm hợp lệ. Ngôi sao ★ là điểm tối ưu.</p>
      </div>
      <div style={{ height: 420 }}>
        <Plot
          data={traces as any}
          layout={layout as any}
          config={{ responsive: true, displayModeBar: false }}
          style={{ width: "100%", height: "100%" }}
        />
      </div>
    </div>
  );
}
