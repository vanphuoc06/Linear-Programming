"use client";
import { useState } from "react";
import InputForm from "@/components/InputForm";
import ResultPanel from "@/components/ResultPanel";
import TableauSteps from "@/components/TableauSteps";
import Chart2D from "@/components/Chart2D";
import { SolveResult } from "@/types";



export default function Home() {
  const [result, setResult] = useState<SolveResult | null>(null);
  const [loading, setLoading] = useState(false);
  const [nVars, setNVars] = useState(2);
  const [method, setMethod] = useState<"standard" | "bland" | "two-phase">("standard");

  return (
    <div style={{ minHeight: "100vh", background: "var(--bg)" }}>
      {/* Header */}
      <header style={{
        borderBottom: "1px solid var(--border)",
        padding: "16px 32px",
        display: "flex",
        alignItems: "center",
        justifyContent: "space-between",
        backdropFilter: "blur(10px)",
        position: "sticky",
        top: 0,
        zIndex: 50,
        background: "rgba(10,15,30,0.85)",
      }}>
        <div style={{ display: "flex", alignItems: "center", gap: "12px" }}>
          <div style={{
            width: 40, height: 40, borderRadius: 10,
            background: "linear-gradient(135deg, var(--accent), var(--accent2))",
            display: "flex", alignItems: "center", justifyContent: "center",
          }}>
            <span style={{ fontSize: 22 }}>🧮</span>
          </div>
          <div>
            <h1 className="gradient-text" style={{ fontSize: 20, fontWeight: 700, lineHeight: 1.2 }}>
              LP Solver
            </h1>
            <p style={{ fontSize: 12, color: "var(--text-muted)" }}>Quy Hoạch Tuyến Tính</p>
          </div>
        </div>
        <div style={{ display: "flex", alignItems: "center", gap: "8px" }}>
          <span style={{
            fontSize: 12, color: "var(--text-muted)", background: "var(--surface2)",
            padding: "4px 14px", borderRadius: 20, border: "1px solid var(--border)",
            lineHeight: 1.8,
          }}>
            Đơn hình • Bland • Two-Phase
            <br />
            <span style={{ opacity: 0.6 }}>Dev by Ngô Văn Phước</span>
          </span>
        </div>
      </header>

      {/* Main content */}
      <main style={{ maxWidth: 1400, margin: "0 auto", padding: "32px 24px" }}>
        {/* Hero */}
        <div style={{ textAlign: "center", marginBottom: 40 }}>
          <h2 style={{ fontSize: 36, fontWeight: 800, marginBottom: 8 }}>
            Giải{" "}
            <span className="gradient-text">Quy Hoạch Tuyến Tính</span>
          </h2>
          <p style={{ color: "var(--text-muted)", fontSize: 16, maxWidth: 600, margin: "0 auto" }}>
            Công cụ tính toán quy hoạch tuyến tính một cách tự động
          </p>
        </div>

        <div style={{ display: "grid", gridTemplateColumns: "minmax(0,1fr) minmax(0,1.2fr)", gap: 24 }}>
          {/* Left: Input */}
          <InputForm
            onResult={(r, n) => { setResult(r); setNVars(n); }}
            setLoading={setLoading}
            loading={loading}
            method={method}
            setMethod={setMethod}
          />

          {/* Right: Result */}
          <div style={{ display: "flex", flexDirection: "column", gap: 24 }}>
            {loading && (
              <div className="card" style={{ display: "flex", alignItems: "center", justifyContent: "center", gap: 12, padding: 48 }}>
                <div style={{
                  width: 32, height: 32, borderRadius: "50%",
                  border: "3px solid var(--border)",
                  borderTopColor: "var(--accent)",
                  animation: "spin 0.7s linear infinite",
                }} />
                <span style={{ color: "var(--text-muted)" }}>Đang tính toán...</span>
              </div>
            )}

            {!loading && result && (
              <>
                <ResultPanel result={result} />
                {nVars === 2 && result.status === "optimal" && (
                  <Chart2D result={result} />
                )}
                {result.steps && result.steps.length > 0 && (
                  <TableauSteps steps={result.steps} nVars={nVars} />
                )}
              </>
            )}

            {!loading && !result && (
              <div className="card" style={{
                display: "flex", flexDirection: "column", alignItems: "center",
                justifyContent: "center", gap: 12, padding: 60,
                border: "2px dashed var(--border)",
                background: "transparent",
              }}>
                <span style={{ fontSize: 48 }}>📊</span>
                <p style={{ color: "var(--text-muted)", fontSize: 14 }}>
                  Nhập bài toán và nhấn <strong style={{ color: "var(--text)" }}>Giải</strong> để xem kết quả
                </p>
              </div>
            )}
          </div>
        </div>
      </main>

      <style>{`@keyframes spin { to { transform: rotate(360deg); } }`}</style>
    </div>
  );
}
