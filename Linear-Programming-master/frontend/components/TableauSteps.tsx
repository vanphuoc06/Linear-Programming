"use client";
import { useState } from "react";
import { TableauStep } from "@/types";
import { ChevronDown, ChevronRight } from "lucide-react";

interface Props {
  steps: TableauStep[];
  nVars: number;
}

export default function TableauSteps({ steps, nVars }: Props) {
  const [expanded, setExpanded] = useState<Set<number>>(new Set([0]));

  const toggle = (i: number) => {
    setExpanded((prev) => {
      const s = new Set(prev);
      if (s.has(i)) {
        s.delete(i);
      } else {
        s.add(i);
      }
      return s;
    });
  };

  // Filter only actual tableau steps (not phase marker steps)
  const tableauSteps = steps.filter((s) => s.rows && s.rows.length > 0);
  const phaseMarkers: Record<number, string> = {};
  let tableauIdx = 0;
  steps.forEach((s) => {
    if (!s.rows && s.note) {
      phaseMarkers[tableauIdx] = s.note;
    } else {
      tableauIdx++;
    }
  });

  if (tableauSteps.length === 0) return null;

  return (
    <div className="card" style={{ display: "flex", flexDirection: "column", gap: 12 }}>
      <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between" }}>
        <h2 style={{ fontSize: 18, fontWeight: 700 }}>🧮 Từng bước Simplex Tableau</h2>
        <div style={{ display: "flex", gap: 8 }}>
          <button className="btn-secondary" onClick={() => setExpanded(new Set(tableauSteps.map((_, i) => i)))} style={{ fontSize: 12, padding: "4px 12px" }}>Mở tất cả</button>
          <button className="btn-secondary" onClick={() => setExpanded(new Set())} style={{ fontSize: 12, padding: "4px 12px" }}>Đóng tất cả</button>
        </div>
      </div>

      {/* Legend */}
      <div style={{ display: "flex", gap: 16, fontSize: 12, color: "var(--text-muted)", flexWrap: "wrap" }}>
        <span style={{ display: "flex", alignItems: "center", gap: 4 }}>
          <span style={{ width: 14, height: 14, background: "rgba(251,191,36,0.3)", borderRadius: 3, display: "inline-block" }} />
          Cột pivot (biến vào)
        </span>
        <span style={{ display: "flex", alignItems: "center", gap: 4 }}>
          <span style={{ width: 14, height: 14, background: "rgba(52,211,153,0.3)", borderRadius: 3, display: "inline-block" }} />
          Hàng pivot (biến ra)
        </span>
        <span style={{ display: "flex", alignItems: "center", gap: 4 }}>
          <span style={{ width: 14, height: 14, background: "rgba(239,68,68,0.4)", borderRadius: 3, display: "inline-block" }} />
          Phần tử trục
        </span>
      </div>

      {tableauSteps.map((step, idx) => {
        const isOpen = expanded.has(idx);
        const marker = phaseMarkers[idx];
        const nCols = step.rows![0].length;
        const nSlack = nCols - 1 - nVars;

        // Build column headers
        const headers = [
          "Cơ sở",
          ...Array.from({ length: nVars }, (_, j) => `x${j + 1}`),
          ...Array.from({ length: nSlack }, (_, j) => `s${j + 1}`),
          "RHS",
        ];

        return (
          <div key={idx}>
            {marker && (
              <div style={{
                background: "linear-gradient(90deg, rgba(99,102,241,0.2), transparent)",
                borderLeft: "3px solid var(--accent)",
                padding: "8px 14px",
                borderRadius: "0 8px 8px 0",
                fontSize: 13,
                fontWeight: 700,
                color: "#c4b5fd",
                marginBottom: 4,
              }}>
                {marker}
              </div>
            )}
            <div style={{ border: "1px solid var(--border)", borderRadius: 10, overflow: "hidden" }}>
              {/* Header */}
              <button onClick={() => toggle(idx)} style={{
                width: "100%", display: "flex", alignItems: "center", justifyContent: "space-between",
                padding: "12px 16px", background: "var(--surface2)", border: "none",
                cursor: "pointer", color: "var(--text)", gap: 8,
              }}>
                <div style={{ display: "flex", alignItems: "center", gap: 10 }}>
                  {isOpen ? <ChevronDown size={16} /> : <ChevronRight size={16} />}
                  <span style={{ fontWeight: 600, fontSize: 14 }}>
                    Bước {idx === 0 ? "0 (Bảng ban đầu)" : idx}
                    {step.point_str && <span style={{ color: "var(--accent)", marginLeft: 6 }}>— Tại {step.point_str}</span>}
                  </span>
                  {idx > 0 && step.pivot_col !== null && step.pivot_col !== undefined && (
                    <span style={{ fontSize: 12, color: "var(--text-muted)", background: "var(--surface)", padding: "2px 8px", borderRadius: 10, border: "1px solid var(--border)" }}>
                      Pivot: cột {step.pivot_col} × hàng {step.pivot_row}
                    </span>
                  )}
                </div>
              </button>

              {/* Content */}
              {isOpen && (
                <div style={{ padding: "16px", overflowX: "auto" }}>
                  {/* Note */}
                  <div style={{
                    background: "var(--surface2)", borderRadius: 8, padding: "10px 14px",
                    fontSize: 13, color: "var(--text-muted)", marginBottom: 14,
                    lineHeight: 1.6, borderLeft: "3px solid var(--accent2)",
                  }}>
                    💬 {step.note}
                  </div>

                  {/* Dictionary Format */}
                  {step.dictionary_str && (
                    <div style={{
                      background: "rgba(0,0,0,0.3)", border: "1px solid var(--border)",
                      borderRadius: 8, padding: "16px", marginBottom: 16,
                      fontFamily: "var(--font-mono), monospace", fontSize: 14,
                      color: "var(--text)", whiteSpace: "pre-wrap", lineHeight: 1.5
                    }}>
                      {step.dictionary_str}
                    </div>
                  )}


                </div>
              )}
            </div>
          </div>
        );
      })}
    </div>
  );
}
