import { useEffect, useState } from "react";
import axios from "axios";

export default function Recommendations() {
  const [data, setData] = useState([]);
  const [summary, setSummary] = useState(null);
  const [loading, setLoading] = useState(true);
  const [days, setDays] = useState(90);
  const [feedback, setFeedback] = useState({}); // { [service]: 'accepted'|'dismissed' }
  const [submitting, setSubmitting] = useState({}); // { [service]: boolean }

  const api = import.meta.env.VITE_API_URL;

  useEffect(() => {
    fetchRecs();
  }, [days]);

  const fetchRecs = async () => {
    setLoading(true);
    try {
      const res = await axios.get(`${api}/api/recommendations`, { params: { days } });
      setData(res.data.data || []);
      setSummary(res.data.summary || null);
    } catch (e) {
      console.error("Error fetching recommendations", e);
    }
    setLoading(false);
  };

  const explain = async (service) => {
    try {
      const res = await axios.get(`${api}/api/recommendations/${encodeURIComponent(service)}/explain`, { params: { days } });
      const msg = res.data?.explanation || "No explanation";
      alert(msg);
    } catch (e) {
      alert("Failed to load explanation");
    }
  };

  const sendFeedback = async (service, action) => {
    try {
      setSubmitting((s) => ({ ...s, [service]: true }));
      const url = `${api}/api/recommendations/${encodeURIComponent(service)}/${action}`;
      const res = await axios.post(url, null);
      if (res.data?.status === "ok") {
        setFeedback((f) => ({ ...f, [service]: action }));
        alert(`${action === "accept" ? "Accepted" : "Dismissed"} recommendation for ${service}`);
      } else {
        alert("Action failed. Please try again.");
      }
    } catch (e) {
      console.error("Feedback error", e);
      alert("Failed to submit action");
    } finally {
      setSubmitting((s) => ({ ...s, [service]: false }));
    }
  };

  return (
    <div style={{ padding: "40px", backgroundColor: "#f9fafb", minHeight: "100vh" }}>
      <div style={{ backgroundColor: "white", padding: "32px", borderRadius: "12px", marginBottom: "24px", boxShadow: "0 2px 12px rgba(0,0,0,0.08)" }}>
        <h1 style={{ fontSize: 36, fontWeight: 800, margin: 0, color: "#111827" }}>AI Recommendations</h1>
        <p style={{ color: "#6b7280", marginTop: 8 }}>Actionable insights derived from spend trends, anomalies and budgets.</p>
        <div style={{ marginTop: 16, display: "flex", gap: 8 }}>
          {[{ label: "30d", v: 30 }, { label: "60d", v: 60 }, { label: "90d", v: 90 }].map((o) => (
            <button key={o.v} onClick={() => setDays(o.v)} style={{ padding: "8px 14px", borderRadius: 8, border: days === o.v ? "2px solid #3b82f6" : "2px solid #e5e7eb", background: days === o.v ? "#eff6ff" : "white", color: days === o.v ? "#2563eb" : "#6b7280", fontWeight: 700 }}>
              {o.label}
            </button>
          ))}
        </div>
      </div>

      {summary && (
        <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(220px, 1fr))", gap: 16, marginBottom: 24 }}>
          {[
            { label: "Services Evaluated", value: summary.services_evaluated, color: "#3b82f6" },
            { label: "Recommendations", value: summary.recommendations, color: "#10b981" },
            { label: "Potential Savings", value: `$${summary.potential_savings_total}`, color: "#f59e0b" },
          ].map((s, i) => (
            <div key={i} style={{ background: "white", borderRadius: 12, padding: 20, border: `2px solid ${s.color}20`, textAlign: "center", boxShadow: "0 1px 8px rgba(0,0,0,0.06)" }}>
              <p style={{ margin: 0, fontSize: 12, color: "#6b7280", fontWeight: 700 }}>{s.label}</p>
              <p style={{ margin: "8px 0 0 0", fontSize: 24, fontWeight: 800, color: s.color }}>{s.value}</p>
            </div>
          ))}
        </div>
      )}

      <div style={{ display: "grid", gap: 16 }}>
        {loading ? (
          <div style={{ background: "white", padding: 40, borderRadius: 12, textAlign: "center", color: "#6b7280" }}>Loading recommendations…</div>
        ) : data.length === 0 ? (
          <div style={{ background: "white", padding: 40, borderRadius: 12, textAlign: "center", color: "#6b7280" }}>No recommendations for the selected window.</div>
        ) : (
          data.map((rec) => (
            <div key={rec.service} style={{ background: "white", borderRadius: 12, padding: 20, boxShadow: "0 1px 10px rgba(0,0,0,0.08)" }}>
              <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: 12 }}>
                <div>
                  <h3 style={{ margin: 0, fontSize: 18, fontWeight: 800, color: "#111827" }}>{rec.service}</h3>
                  <p style={{ margin: 0, color: "#6b7280", fontSize: 13 }}>
                    Priority: <span style={{ fontWeight: 800, color: rec.priority_score > 70 ? "#dc2626" : rec.priority_score > 40 ? "#f59e0b" : "#10b981" }}>{rec.priority_score}</span>
                    {rec.potential_savings_usd ? ` • Potential $${rec.potential_savings_usd}` : ""}
                    {feedback[rec.service] && (
                      <span style={{ marginLeft: 8, padding: "2px 8px", borderRadius: 999, fontSize: 12, fontWeight: 700, color: feedback[rec.service] === "accept" ? "#065f46" : "#7c2d12", background: feedback[rec.service] === "accept" ? "#d1fae5" : "#ffedd5", border: `1px solid ${feedback[rec.service] === "accept" ? "#10b981" : "#fb923c"}` }}>
                        {feedback[rec.service] === "accept" ? "Accepted" : "Dismissed"}
                      </span>
                    )}
                  </p>
                </div>
                <div style={{ display: "flex", gap: 8 }}>
                  <button onClick={() => explain(rec.service)} style={{ padding: "8px 12px", borderRadius: 8, border: "2px solid #e5e7eb", background: "white", fontWeight: 700, color: "#374151" }}>Explain</button>
                  <button
                    onClick={() => sendFeedback(rec.service, "accept")}
                    disabled={submitting[rec.service] || feedback[rec.service] === "accept"}
                    style={{ padding: "8px 12px", borderRadius: 8, border: "2px solid #e5e7eb", background: submitting[rec.service] || feedback[rec.service] === "accept" ? "#f9fafb" : "#ecfeff", fontWeight: 700, color: submitting[rec.service] || feedback[rec.service] === "accept" ? "#9ca3af" : "#047857", cursor: submitting[rec.service] || feedback[rec.service] === "accept" ? "not-allowed" : "pointer" }}
                  >
                    {submitting[rec.service] ? "Submitting…" : feedback[rec.service] === "accept" ? "Accepted" : "Accept"}
                  </button>
                  <button
                    onClick={() => sendFeedback(rec.service, "dismiss")}
                    disabled={submitting[rec.service] || feedback[rec.service] === "dismiss"}
                    style={{ padding: "8px 12px", borderRadius: 8, border: "2px solid #e5e7eb", background: submitting[rec.service] || feedback[rec.service] === "dismiss" ? "#f9fafb" : "#fff7ed", fontWeight: 700, color: submitting[rec.service] || feedback[rec.service] === "dismiss" ? "#9ca3af" : "#b45309", cursor: submitting[rec.service] || feedback[rec.service] === "dismiss" ? "not-allowed" : "pointer" }}
                  >
                    {submitting[rec.service] ? "Submitting…" : feedback[rec.service] === "dismiss" ? "Dismissed" : "Dismiss"}
                  </button>
                </div>
              </div>

              <div style={{ display: "grid", gap: 10 }}>
                {rec.issues.map((issue, idx) => (
                  <div key={idx} style={{ border: "1px solid #e5e7eb", borderRadius: 10, padding: 12, background: "#fbfdff" }}>
                    <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
                      <strong style={{ color: "#111827" }}>{issue.title}</strong>
                      <span style={{ fontSize: 12, color: "#6b7280" }}>{issue.code}</span>
                    </div>
                    <p style={{ margin: "6px 0 0 0", color: "#374151", fontSize: 13 }}>{issue.evidence}</p>
                    <p style={{ margin: "6px 0 0 0", color: "#2563eb", fontSize: 13, fontWeight: 600 }}>{issue.recommended_action}</p>
                  </div>
                ))}
              </div>
            </div>
          ))
        )}
      </div>
    </div>
  );
}
