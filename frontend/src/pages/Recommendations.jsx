import { useEffect, useState } from "react";
import axios from "axios";

export default function Recommendations() {
  const [data, setData] = useState([]);
  const [summary, setSummary] = useState(null);
  const [loading, setLoading] = useState(true);
  const [days, setDays] = useState(90);
  const [feedback, setFeedback] = useState({}); // { [service]: 'accepted'|'dismissed' }
  const [submitting, setSubmitting] = useState({}); // { [service]: boolean }
  const [alerts, setAlerts] = useState([]); // recent alerts

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
      // Aggregate feedback preload
      preloadAggregateFeedback();
      fetchAlerts();
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

  const fetchAlerts = async () => {
    try {
      const res = await axios.get(`${api}/api/recommendations/alerts`, { params: { days: 30, limit: 200 } });
      setAlerts(res.data?.data || []);
    } catch (e) {
      console.warn("Failed to fetch alerts", e);
    }
  };

  const latestAlertFor = (service) => {
    const row = alerts.find(a => a.service === service);
    return row || null;
  };

  const priorityBadge = (rec) => {
    const boosted = rec.feedback_action === 'accept' && rec.priority_score > rec.base_priority_score;
    const suppressed = rec.feedback_action === 'dismiss' && rec.priority_score < rec.base_priority_score;
    const alertActive = rec.priority_score >= 70; // threshold aligned with backend default
    const alertSent = rec.alert_sent;
    const recovered = rec.alert_recovered;
    let text = '';
    let style = {};
    if (recovered) {
      text = 'Recovered';
      style = { background: '#ecfdf5', color: '#065f46', border: '1px solid #10b981' };
    } else if (alertSent || alertActive) {
      text = 'High Alert';
      style = { background: '#fef2f2', color: '#991b1b', border: '1px solid #dc2626' };
    } else if (boosted) {
      text = 'Boosted';
      style = { background: '#eff6ff', color: '#1d4ed8', border: '1px solid #3b82f6' };
    } else if (suppressed) {
      text = 'Suppressed';
      style = { background: '#f3f4f6', color: '#374151', border: '1px solid #9ca3af' };
    }
    if (!text) return null;
    return <span style={{ marginLeft: 8, padding: '2px 8px', borderRadius: 999, fontSize: 11, fontWeight: 700, ...style }}>{text}</span>;
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

  const preloadAggregateFeedback = async () => {
    try {
      const res = await axios.get(`${api}/api/recommendations/feedback/aggregate`);
      const rows = res.data?.data || [];
      const map = {};
      rows.forEach(r => {
        if (r.last_feedback_action) {
          map[r.service] = r.last_feedback_action;
        }
      });
      setFeedback(map);
    } catch (e) {
      console.warn("Aggregate feedback preload failed", e);
    }
  };

  const exportCSV = async () => {
    try {
      const res = await axios.get(`${api}/api/recommendations/export`, { params: { days }, responseType: 'blob' });
      const url = window.URL.createObjectURL(new Blob([res.data], { type: 'text/csv' }));
      const a = document.createElement('a');
      a.href = url;
      a.download = `recommendations_${days}d.csv`;
      document.body.appendChild(a);
      a.click();
      a.remove();
      window.URL.revokeObjectURL(url);
    } catch (e) {
      alert('Failed to export CSV');
    }
  };

  return (
    <div style={{ minHeight: "100vh" }}>
      <div style={{ backgroundColor: "white", padding: "32px", borderRadius: "12px", marginBottom: "24px" }}>
        <h1 style={{ fontSize: 36, fontWeight: 800, margin: 0, color: "#111827" }}>AI Recommendations</h1>
        <p style={{ color: "#6b7280", marginTop: 8 }}>Actionable insights derived from spend trends, anomalies and budgets.</p>
        <div style={{ marginTop: 16, display: "flex", gap: 8 }}>
          {[{ label: "30d", v: 30 }, { label: "60d", v: 60 }, { label: "90d", v: 90 }].map((o) => (
            <button key={o.v} onClick={() => setDays(o.v)} style={{ padding: "8px 14px", borderRadius: 8, border: days === o.v ? "2px solid #3b82f6" : "2px solid #e5e7eb", background: days === o.v ? "#eff6ff" : "white", color: days === o.v ? "#2563eb" : "#6b7280", fontWeight: 700 }}>
              {o.label}
            </button>
          ))}
          <button onClick={exportCSV} style={{ padding: "8px 14px", borderRadius: 8, border: "2px solid #059669", background: "#ECFDF5", color: "#047857", fontWeight: 700 }}>
            Download CSV
          </button>
        </div>
        {/* Legend */}
        <div style={{ marginTop: 24, display: 'flex', flexWrap: 'wrap', gap: 10, fontSize: 12 }}>
          {[
            { text: 'High Alert', style: { background: '#fef2f2', color: '#991b1b', border: '1px solid #dc2626' }, desc: 'Priority >= threshold (default 70).' },
            { text: 'Recovered', style: { background: '#ecfdf5', color: '#065f46', border: '1px solid #10b981' }, desc: 'Previously high; now below threshold.' },
            { text: 'Boosted', style: { background: '#eff6ff', color: '#1d4ed8', border: '1px solid #3b82f6' }, desc: 'Accepted & signals persist.' },
            { text: 'Suppressed', style: { background: '#f3f4f6', color: '#374151', border: '1px solid #9ca3af' }, desc: 'Dismissed within cooldown.' },
            { text: 'Accepted', style: { background: '#d1fae5', color: '#065f46', border: '1px solid #10b981' }, desc: 'User accepted recommendation.' },
            { text: 'Dismissed', style: { background: '#ffedd5', color: '#7c2d12', border: '1px solid #fb923c' }, desc: 'User dismissed recommendation.' },
          ].map(b => (
            <span key={b.text} title={b.desc} style={{ display: 'flex', alignItems: 'center', gap: 6 }}>
              <span style={{ padding: '2px 8px', borderRadius: 999, fontWeight: 700, ...b.style }}>{b.text}</span>
            </span>
          ))}
        </div>
      </div>

      {summary && (
        <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(220px, 1fr))", gap: 16, marginBottom: 24 }}>
          {(() => {
            const highAlerts = data.filter(r => r.priority_score >= 70).length;
            const recovered = data.filter(r => r.alert_recovered).length;
            return [
              { label: "Services Evaluated", value: summary.services_evaluated, color: "#3b82f6" },
              { label: "Recommendations", value: summary.recommendations, color: "#10b981" },
              { label: "Potential Savings", value: `$${summary.potential_savings_total}`, color: "#f59e0b" },
              { label: "High Alerts", value: highAlerts, color: "#dc2626" },
              { label: "Recovered", value: recovered, color: "#10b981" },
            ];
          })().map((s, i) => (
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
            <div
              key={rec.service}
              style={{
                background: 'white',
                borderRadius: 12,
                padding: 20,
                boxShadow: '0 1px 10px rgba(0,0,0,0.08)',
                border: rec.feedback_action === 'dismiss' && rec.priority_score < rec.base_priority_score
                  ? '2px solid #e5e7eb'
                  : rec.feedback_action === 'accept' && rec.priority_score > rec.base_priority_score
                    ? '2px solid #3b82f6'
                    : rec.priority_score >= 70 ? '2px solid #dc2626' : '1px solid #e5e7eb'
              }}
            >
              <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: 12 }}>
                <div>
                  <h3 style={{ margin: 0, fontSize: 18, fontWeight: 800, color: "#111827" }}>{rec.service}</h3>
                  <p style={{ margin: 0, color: "#6b7280", fontSize: 13 }}>
                    Priority:{' '}
                    <span
                      title={`Adjusted ${rec.priority_score} vs base ${rec.base_priority_score}${rec.feedback_effect ? ' • ' + rec.feedback_effect : ''}`}
                      style={{ fontWeight: 800, color: rec.priority_score > 70 ? "#dc2626" : rec.priority_score > 40 ? "#f59e0b" : "#10b981" }}
                    >
                      {rec.priority_score}
                    </span>
                    {rec.potential_savings_usd ? ` • Potential $${rec.potential_savings_usd}` : ""}
                    {priorityBadge(rec)}
                    {feedback[rec.service] && (
                      <span style={{ marginLeft: 8, padding: "2px 8px", borderRadius: 999, fontSize: 12, fontWeight: 700, color: feedback[rec.service] === "accept" ? "#065f46" : "#7c2d12", background: feedback[rec.service] === "accept" ? "#d1fae5" : "#ffedd5", border: `1px solid ${feedback[rec.service] === "accept" ? "#10b981" : "#fb923c"}` }} title={feedback[rec.service] === 'accept' ? 'Accepted: monitoring for persistence.' : 'Dismissed: temporarily suppressed.'}>
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
                    <p style={{ margin: "6px 0 0 0", fontSize: 12 }}>
                      <a href="#service-trends" style={{ color: "#1d4ed8", fontWeight: 600 }} title="Jump to service trends tab" onClick={(e) => { e.preventDefault(); /* naive tab switch by simulating click */ const btns=[...document.querySelectorAll('button')].filter(b=>b.textContent==='Service Trends'); if(btns[0]) btns[0].click(); }}>
                        View service trends
                      </a>
                    </p>
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
