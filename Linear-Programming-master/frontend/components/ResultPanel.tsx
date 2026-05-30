"use client";
import { SolveResult } from "@/types";
import { AlertTriangle, CheckCircle, Infinity, XCircle, Layers, RefreshCw } from "lucide-react";

interface Props { result: SolveResult }

const STATUS_CONFIG = {
  optimal: {
    icon: <CheckCircle size={18} />,
    label: "Nghiệm tối ưu duy nhất",
    badgeClass: "badge-optimal",
    emoji: "✅",
  },
  multiple: {
    icon: <Layers size={18} />,
    label: "Vô số nghiệm tối ưu",
    badgeClass: "badge-multiple",
    emoji: "🔵",
  },
  infeasible: {
    icon: <XCircle size={18} />,
    label: "Vô nghiệm (Infeasible)",
    badgeClass: "badge-infeasible",
    emoji: "❌",
  },
  unbounded: {
    icon: <Infinity size={18} />,
    label: "Không giới hạn (Unbounded)",
    badgeClass: "badge-unbounded",
    emoji: "♾️",
  },
  cycling: {
    icon: <RefreshCw size={18} />,
    label: "Phát hiện lặp vòng (Cycling)",
    badgeClass: "badge-cycling",
    emoji: "🔴",
  },
  method_error: {
    icon: <AlertTriangle size={18} />,
    label: "Lỗi phương pháp",
    badgeClass: "badge-method_error",
    emoji: "⚠️",
  },
};

export default function ResultPanel({ result }: Props) {
  const cfg = STATUS_CONFIG[result.status] || STATUS_CONFIG.method_error;

  const isCycling = result.status === "cycling";
  const isMethodError = result.status === "method_error";
  const hasValue = result.optimal_value !== null && result.optimal_value !== undefined;
  const hasSolution = result.solution && Object.keys(result.solution).length > 0;

  const decisionVars = hasSolution
    ? Object.entries(result.solution).filter(([k]) => k.startsWith("x"))
    : [];
  const slackVars = hasSolution
    ? Object.entries(result.solution).filter(([k]) => k.startsWith("s"))
    : [];

  return (
    <div className="card" style={{ display: "flex", flexDirection: "column", gap: 20 }}>
      <h2 style={{ fontSize: 18, fontWeight: 700 }}>📊 Kết quả</h2>

      {/* Status badge */}
      <div style={{ display: "flex", alignItems: "flex-start", gap: 12 }}>
        <span className={`badge ${cfg.badgeClass}`} style={{ fontSize: 14 }}>
          {cfg.icon}
          {cfg.label}
        </span>
      </div>

      {/* Message */}
      <div style={{
        background: (isCycling || isMethodError)
          ? "rgba(239,68,68,0.08)"
          : "var(--surface2)",
        border: `1px solid ${(isCycling || isMethodError) ? "rgba(239,68,68,0.3)" : "var(--border)"}`,
        borderRadius: 10,
        padding: "14px 16px",
        fontSize: 14,
        lineHeight: 1.6,
        color: (isCycling || isMethodError) ? "#fca5a5" : "var(--text)",
      }}>
        {isCycling && (
          <div style={{ marginBottom: 8, fontWeight: 700, color: "#f87171", display: "flex", alignItems: "center", gap: 6 }}>
            <RefreshCw size={16} /> CẢNH BÁO: Bài toán bị lặp vòng vô hạn!
          </div>
        )}
        {result.message}
        {isCycling && (
          <div style={{ marginTop: 10, padding: "8px 12px", background: "rgba(99,102,241,0.1)", borderRadius: 8, color: "#a5b4fc", fontSize: 13 }}>
            💡 Gợi ý: Chuyển sang phương pháp <strong>Quy tắc Bland</strong> để tránh lặp vòng.
          </div>
        )}
      </div>

      {/* Optimal value */}
      {hasValue && (
        <div style={{
          background: "linear-gradient(135deg, rgba(99,102,241,0.15), rgba(139,92,246,0.15))",
          border: "1px solid rgba(99,102,241,0.3)",
          borderRadius: 12,
          padding: "20px 24px",
          textAlign: "center",
        }}>
          <div style={{ fontSize: 12, color: "var(--text-muted)", marginBottom: 6, textTransform: "uppercase", letterSpacing: "0.08em" }}>
            Giá trị tối ưu
          </div>
          <div className="fraction" style={{ fontSize: 36, fontWeight: 800, color: "white" }}>
            Z* = {result.optimal_value}
          </div>
        </div>
      )}

      {/* Decision variables */}
      {decisionVars.length > 0 && (
        <div>
          <div style={{ fontSize: 12, color: "var(--text-muted)", fontWeight: 600, marginBottom: 10, textTransform: "uppercase", letterSpacing: "0.05em" }}>
            Biến quyết định
          </div>
          <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fill, minmax(120px, 1fr))", gap: 10 }}>
            {decisionVars.map(([key, val]) => (
              <div key={key} style={{
                background: "var(--surface2)", borderRadius: 10,
                padding: "12px 16px", textAlign: "center",
                border: "1px solid var(--border)",
              }}>
                <div style={{ fontSize: 12, color: "var(--text-muted)", marginBottom: 4 }}>{key}</div>
                <div className="fraction" style={{ fontSize: 22, fontWeight: 700, color: "#a5b4fc" }}>
                  {val}
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Slack variables */}
      {slackVars.length > 0 && (
        <div>
          <div style={{ fontSize: 12, color: "var(--text-muted)", fontWeight: 600, marginBottom: 8, textTransform: "uppercase", letterSpacing: "0.05em" }}>
            Biến bù (Slack / Surplus)
          </div>
          <div style={{ display: "flex", flexWrap: "wrap", gap: 8 }}>
            {slackVars.map(([key, val]) => (
              <span key={key} className="fraction" style={{
                background: "var(--surface2)", borderRadius: 8,
                padding: "6px 14px", fontSize: 13,
                border: "1px solid var(--border)",
                color: "var(--text-muted)",
              }}>
                {key} = {val}
              </span>
            ))}
          </div>
        </div>
      )}

      {/* Multiple optima note */}
      {result.status === "multiple" && (
        <div style={{ background: "rgba(59,130,246,0.08)", border: "1px solid rgba(59,130,246,0.2)", borderRadius: 8, padding: "12px 16px", fontSize: 13, color: "#93c5fd" }}>
          ℹ️ Tồn tại vô số bộ nghiệm cùng đạt giá trị Z* này. Nghiệm hiển thị là một trong các nghiệm tối ưu.
        </div>
      )}
    </div>
  );
}
