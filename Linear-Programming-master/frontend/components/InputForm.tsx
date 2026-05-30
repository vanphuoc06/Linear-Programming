"use client";
import { useState } from "react";
import { Constraint, SolveResult } from "@/types";
// ─── Example problems ────────────────────────────────────────────────────────
const EXAMPLES = [
  {
    label: "Ví dụ 1 — Maximize 2 biến (có đồ thị)",
    objective: "max" as const,
    method: "standard" as const,
    c: [3, 5],
    constraints: [
      { coeffs: [1, 0], type: "<=" as const, rhs: 4 },
      { coeffs: [0, 2], type: "<=" as const, rhs: 12 },
      { coeffs: [3, 2], type: "<=" as const, rhs: 18 },
    ],
  },
  {
    label: "Ví dụ 2 — Vô số nghiệm tối ưu",
    objective: "max" as const,
    method: "standard" as const,
    c: [2, 4],
    constraints: [
      { coeffs: [1, 2], type: "<=" as const, rhs: 8 },
      { coeffs: [1, 0], type: "<=" as const, rhs: 4 },
      { coeffs: [0, 1], type: "<=" as const, rhs: 3 },
    ],
  },
  {
    label: "Ví dụ 3 — Two-Phase (có ràng buộc ≥ và =)",
    objective: "min" as const,
    method: "two-phase" as const,
    c: [2, 3, 4],
    constraints: [
      { coeffs: [3, 1, 1], type: ">=" as const, rhs: 6 },
      { coeffs: [1, 2, 1], type: ">=" as const, rhs: 8 },
      { coeffs: [1, 1, 1], type: "=" as const, rhs: 5 },
    ],
  },
];

interface Props {
  onResult: (result: SolveResult, nVars: number, payload: object) => void;
  setLoading: (v: boolean) => void;
  loading: boolean;
  method: "standard" | "bland" | "two-phase";
  setMethod: (m: "standard" | "bland" | "two-phase") => void;
}

export default function InputForm({ onResult, setLoading, loading, method, setMethod }: Props) {
  const [nVars, setNVars] = useState(2);
  const [nCons, setNCons] = useState(3);
  const [objective, setObjective] = useState<"max" | "min">("max");
  const [showSteps, setShowSteps] = useState(true);
  const [c, setC] = useState<(number | "")[]>([3, 5]);
  const [constraints, setConstraints] = useState<Constraint[]>([
    { coeffs: [1, 0], type: "<=", rhs: 4 },
    { coeffs: [0, 2], type: "<=", rhs: 12 },
    { coeffs: [3, 2], type: "<=", rhs: 18 },
  ]);
  const [errors, setErrors] = useState<string[]>([]);
  const [showExamples, setShowExamples] = useState(false);

  // ── Helpers ──────────────────────────────────────────────────────────────

  const resize = (newN: number, newM: number) => {
    setNVars(newN);
    setNCons(newM);
    setC((prev) => {
      const arr = [...prev];
      while (arr.length < newN) arr.push("");
      return arr.slice(0, newN);
    });
    setConstraints((prev) => {
      const rows = [...prev];
      while (rows.length < newM)
        rows.push({ coeffs: Array(newN).fill(""), type: "<=", rhs: "" });
      const sliced = rows.slice(0, newM);
      return sliced.map((r) => {
        const coeffs = [...r.coeffs];
        while (coeffs.length < newN) coeffs.push("");
        return { ...r, coeffs: coeffs.slice(0, newN) };
      });
    });
  };

  const loadExample = (ex: typeof EXAMPLES[0]) => {
    const n = ex.c.length;
    const m = ex.constraints.length;
    setNVars(n);
    setNCons(m);
    setObjective(ex.objective);
    setMethod(ex.method);
    setC(ex.c);
    setConstraints(ex.constraints.map((c) => ({ ...c, coeffs: [...c.coeffs] })));
    setShowExamples(false);
    setErrors([]);
  };

  // ── Validation ───────────────────────────────────────────────────────────

  const validate = (): boolean => {
    const errs: string[] = [];
    for (let j = 0; j < nVars; j++) {
      if (c[j] === "" || c[j] === undefined || isNaN(Number(c[j])))
        errs.push(`Hàm mục tiêu: hệ số biến x${j + 1} không hợp lệ.`);
    }
    constraints.forEach((con, i) => {
      con.coeffs.forEach((v, j) => {
        if (v === "" || isNaN(Number(v)))
          errs.push(`Ràng buộc ${i + 1}: hệ số x${j + 1} không hợp lệ.`);
      });
      if (con.rhs === "" || isNaN(Number(con.rhs)))
        errs.push(`Ràng buộc ${i + 1}: vế phải (RHS) không hợp lệ.`);
    });
    setErrors(errs);
    return errs.length === 0;
  };

  // ── Submit ───────────────────────────────────────────────────────────────

  const handleSolve = async () => {
    if (!validate()) return;
    setLoading(true);
    setErrors([]);
    try {
      const body = {
        method,
        objective,
        c: c.map(Number),
        constraints: constraints.map((con) => ({
          coeffs: con.coeffs.map(Number),
          type: con.type,
          rhs: Number(con.rhs),
        })),
        bounds: Array(nVars).fill([0, null]),
        show_steps: showSteps,
      };
      const res = await fetch("/api/solve", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(body),
      });
      if (!res.ok) {
        const err = await res.json();
        throw new Error(err.detail || "Lỗi server.");
      }
      const data: SolveResult = await res.json();
      // Attach input data for chart
      data.c = c.map(Number);
      data.constraints = constraints.map((con) => ({
        coeffs: con.coeffs.map(Number),
        type: con.type,
        rhs: Number(con.rhs),
      }));
      onResult(data, nVars, body);
    } catch (e: any) {
      setErrors([e.message || "Không thể kết nối tới server. Hãy đảm bảo backend đang chạy."]);
    } finally {
      setLoading(false);
    }
  };

  // ── UI ───────────────────────────────────────────────────────────────────

  const labelStyle = { fontSize: 12, color: "var(--text-muted)", fontWeight: 600, marginBottom: 6, display: "block", textTransform: "uppercase" as const, letterSpacing: "0.05em" };
  const rowStyle = { display: "flex", gap: 8, alignItems: "center" };

  return (
    <div className="card" style={{ display: "flex", flexDirection: "column", gap: 20 }}>
      {/* Title row */}
      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
        <h2 style={{ fontSize: 18, fontWeight: 700 }}>📝 Nhập bài toán</h2>
        {/* Load example dropdown */}
        <div style={{ position: "relative" }}>
          <button className="btn-secondary" onClick={() => setShowExamples(!showExamples)}
            style={{ display: "flex", alignItems: "center", gap: 6 }}>
            📖 Bài mẫu ▼
          </button>
          {showExamples && (
            <div style={{
              position: "absolute", right: 0, top: "110%", zIndex: 100,
              background: "var(--surface2)", border: "1px solid var(--border)",
              borderRadius: 10, overflow: "hidden", minWidth: 280,
            }}>
              {EXAMPLES.map((ex, i) => (
                <button key={i} onClick={() => loadExample(ex)} style={{
                  display: "block", width: "100%", textAlign: "left",
                  padding: "10px 16px", background: "transparent",
                  border: "none", color: "var(--text)", fontSize: 13,
                  cursor: "pointer", borderBottom: "1px solid var(--border)",
                  transition: "background 0.15s",
                }}
                  onMouseEnter={(e) => (e.currentTarget.style.background = "var(--surface)")}
                  onMouseLeave={(e) => (e.currentTarget.style.background = "transparent")}>
                  {ex.label}
                </button>
              ))}
            </div>
          )}
        </div>
      </div>

      {/* Config row */}
      <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 12 }}>
        <div>
          <label style={labelStyle}>Số biến (n)</label>
          <input type="number" min={1} max={10} className="lp-input" value={nVars}
            onChange={(e) => resize(Math.max(1, Math.min(10, +e.target.value || 1)), nCons)} />
        </div>
        <div>
          <label style={labelStyle}>Số ràng buộc (m)</label>
          <input type="number" min={1} max={15} className="lp-input" value={nCons}
            onChange={(e) => resize(nVars, Math.max(1, Math.min(15, +e.target.value || 1)))} />
        </div>
        <div>
          <label style={labelStyle}>Mục tiêu tối ưu</label>
          <select className="lp-select" style={{ width: "100%" }} value={objective}
            onChange={(e) => setObjective(e.target.value as "max" | "min")}>
            <option value="max">Maximize — Max Z</option>
            <option value="min">Minimize — Min Z</option>
          </select>
        </div>
        <div>
          <label style={labelStyle}>Phương pháp giải</label>
          <select className="lp-select" style={{ width: "100%" }} value={method}
            onChange={(e) => setMethod(e.target.value as any)}>
            <option value="standard">Đơn hình cơ bản (Standard)</option>
            <option value="bland">Đơn hình Bland&apos;s Rule</option>
            <option value="two-phase">Đơn hình 2 pha (Two-Phase)</option>
          </select>
        </div>
      </div>

      {/* Method description */}
      <div style={{ background: "var(--surface2)", borderRadius: 8, padding: "10px 14px", fontSize: 12, color: "var(--text-muted)", borderLeft: "3px solid var(--accent)" }}>
        {method === "standard" && "📌 Đơn hình cơ bản: Chọn cột vào theo hệ số âm nhỏ nhất. Chỉ dùng cho ràng buộc ≤. Có thể bị lặp vòng."}
        {method === "bland" && "🛡️ Quy tắc Bland: Chọn biến vào có chỉ số nhỏ nhất. Đảm bảo hội tụ, tránh lặp vòng. Chỉ dùng cho ràng buộc ≤."}
        {method === "two-phase" && "⚡ Đơn hình 2 pha: Pha 1 tìm nghiệm cơ sở ban đầu (dùng biến giả), Pha 2 tối ưu bài gốc. Dùng được cho mọi loại ràng buộc (≤, ≥, =)."}
      </div>

      {/* Objective function */}
      <div>
        <label style={labelStyle}>Hàm mục tiêu — {objective === "max" ? "Maximize" : "Minimize"} Z =</label>
        <div style={{ display: "flex", gap: 6, flexWrap: "wrap", alignItems: "center" }}>
          {c.map((ci, j) => (
            <div key={j} style={rowStyle}>
              <input type="number" className="lp-input" style={{ width: 70 }} value={ci}
                onChange={(e) => {
                  const arr = [...c];
                  arr[j] = e.target.value === "" ? "" : Number(e.target.value);
                  setC(arr);
                }}
                placeholder={`c${j + 1}`}
              />
              <span style={{ color: "var(--text-muted)", fontSize: 13 }}>
                x<sub>{j + 1}</sub>
                {j < nVars - 1 ? " +" : ""}
              </span>
            </div>
          ))}
        </div>
      </div>

      {/* Constraints */}
      <div>
        <label style={labelStyle}>Ràng buộc</label>
        <div style={{ display: "flex", flexDirection: "column", gap: 8 }}>
          {constraints.map((con, i) => (
            <div key={i} style={{ display: "flex", gap: 6, alignItems: "center", background: "var(--surface2)", padding: "8px 12px", borderRadius: 8 }}>
              <span style={{ color: "var(--text-muted)", fontSize: 12, minWidth: 24 }}>{i + 1}.</span>
              {con.coeffs.map((v, j) => (
                <div key={j} style={rowStyle}>
                  <input type="number" className="lp-input" style={{ width: 60 }} value={v}
                    onChange={(e) => {
                      const nc = [...constraints];
                      nc[i] = { ...nc[i], coeffs: nc[i].coeffs.map((old, jj) => jj === j ? (e.target.value === "" ? "" : Number(e.target.value)) : old) };
                      setConstraints(nc);
                    }}
                    placeholder={`a${i + 1}${j + 1}`}
                  />
                  <span style={{ color: "var(--text-muted)", fontSize: 12 }}>
                    x<sub>{j + 1}</sub>
                    {j < nVars - 1 ? " +" : ""}
                  </span>
                </div>
              ))}
              <select className="lp-select" value={con.type}
                onChange={(e) => {
                  const nc = [...constraints];
                  nc[i] = { ...nc[i], type: e.target.value as any };
                  setConstraints(nc);
                }}>
                <option value="<=">≤</option>
                <option value=">=">≥</option>
                <option value="=">＝</option>
              </select>
              <input type="number" className="lp-input" style={{ width: 70 }} value={con.rhs}
                onChange={(e) => {
                  const nc = [...constraints];
                  nc[i] = { ...nc[i], rhs: e.target.value === "" ? "" : Number(e.target.value) };
                  setConstraints(nc);
                }}
                placeholder="b" />
            </div>
          ))}
        </div>
        <div style={{ marginTop: 8, fontSize: 12, color: "var(--text-muted)" }}>
          Tất cả biến mặc định: x<sub>i</sub> ≥ 0
        </div>
      </div>

      {/* Show steps toggle */}
      <label style={{ display: "flex", alignItems: "center", gap: 10, cursor: "pointer", fontSize: 14 }}>
        <div onClick={() => setShowSteps(!showSteps)} style={{
          width: 40, height: 22, borderRadius: 11,
          background: showSteps ? "var(--accent)" : "var(--border)",
          position: "relative", transition: "background 0.2s",
        }}>
          <div style={{
            position: "absolute", top: 3, left: showSteps ? 21 : 3,
            width: 16, height: 16, borderRadius: "50%", background: "white",
            transition: "left 0.2s",
          }} />
        </div>
        Hiển thị từng bước Simplex Tableau
      </label>

      {/* Errors */}
      {errors.length > 0 && (
        <div style={{ background: "rgba(239,68,68,0.1)", border: "1px solid rgba(239,68,68,0.3)", borderRadius: 8, padding: "12px 16px" }}>
          {errors.map((e, i) => (
            <p key={i} style={{ color: "#f87171", fontSize: 13, marginBottom: 4 }}>⚠ {e}</p>
          ))}
        </div>
      )}

      {/* Solve button */}
      <button className="btn-primary" onClick={handleSolve} disabled={loading}
        style={{ width: "100%", justifyContent: "center", padding: "14px", fontSize: 16 }}>
        {loading ? "Đang tính toán..." : "▶ Giải bài toán"}
      </button>
    </div>
  );
}
