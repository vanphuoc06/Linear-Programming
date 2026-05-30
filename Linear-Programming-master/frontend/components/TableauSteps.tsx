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

  // Filter steps that have note (QHTT format returns text notes/dictionaries instead of rows)
  const displaySteps = steps.filter((s) => s.note || s.dictionary_str);
  
  if (displaySteps.length === 0) return null;

  return (
    <div className="card" style={{ display: "flex", flexDirection: "column", gap: 12 }}>
      <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between" }}>
        <h2 style={{ fontSize: 18, fontWeight: 700 }}>🧮 Các bước giải (Từ vựng)</h2>
        <div style={{ display: "flex", gap: 8 }}>
          <button className="btn-secondary" onClick={() => setExpanded(new Set(displaySteps.map((_, i) => i)))} style={{ fontSize: 12, padding: "4px 12px" }}>Mở tất cả</button>
          <button className="btn-secondary" onClick={() => setExpanded(new Set())} style={{ fontSize: 12, padding: "4px 12px" }}>Đóng tất cả</button>
        </div>
      </div>

      {displaySteps.map((step, idx) => {
        const isOpen = expanded.has(idx);

        return (
          <div key={idx}>
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
                  {/* Content */}
                  <div style={{
                    background: "rgba(0,0,0,0.3)", border: "1px solid var(--border)",
                    borderRadius: 8, padding: "16px", marginBottom: 16,
                    fontFamily: "var(--font-mono), monospace", fontSize: 13,
                    color: "var(--text)", whiteSpace: "pre-wrap", lineHeight: 1.5,
                    overflowX: "auto"
                  }}>
                    {step.note}
                  </div>


                </div>
              )}
            </div>
          </div>
        );
      })}
    </div>
  );
}
