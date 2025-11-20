import { useEffect, useState } from "react";
import axios from "axios";

export default function Settings() {
  const [settings, setSettings] = useState({});
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [message, setMessage] = useState(null);

  const api = import.meta.env.VITE_API_URL;

  useEffect(() => {
    fetchSettings();
  }, []);

  const fetchSettings = async () => {
    setLoading(true);
    try {
      const res = await axios.get(`${api}/api/recommendations/settings`);
      setSettings(res.data?.data || {});
    } catch (e) {
      console.error("Failed to load settings", e);
      setMessage({ type: "error", text: "Failed to load settings" });
    }
    setLoading(false);
  };

  const handleChange = (key, value) => {
    setSettings((s) => ({ ...s, [key]: value }));
  };

  const handleSave = async () => {
    setSaving(true);
    setMessage(null);
    try {
      const res = await axios.patch(`${api}/api/recommendations/settings`, settings);
      setSettings(res.data?.data || settings);
      setMessage({ type: "success", text: "Settings saved successfully!" });
    } catch (e) {
      console.error("Failed to save settings", e);
      setMessage({ type: "error", text: "Failed to save settings" });
    }
    setSaving(false);
  };

  const handleReset = () => {
    fetchSettings();
    setMessage(null);
  };

  const fields = [
    { key: "RECOMMENDATION_ALERT_THRESHOLD", label: "Alert Threshold", desc: "Priority score triggering high-priority alert (0-100)", type: "number", min: 0, max: 100 },
    { key: "RECOMMENDATION_ALERT_COOLDOWN_DAYS", label: "Alert Cooldown (days)", desc: "Minimum days between repeat alerts for same service", type: "number", min: 1, max: 365 },
    { key: "RECOMMENDATION_RECOVERY_DAYS", label: "Recovery Window (days)", desc: "Days below threshold before marking recovered", type: "number", min: 1, max: 90 },
    { key: "FEEDBACK_DISMISS_COOLDOWN_DAYS", label: "Dismiss Cooldown (days)", desc: "Suppression duration after user dismisses", type: "number", min: 1, max: 365 },
    { key: "FEEDBACK_ACCEPT_BOOST", label: "Accept Boost", desc: "Priority points added when accepted and issue persists", type: "number", min: 0, max: 50 },
    { key: "FEEDBACK_DISMISS_PENALTY_FACTOR", label: "Dismiss Penalty Factor", desc: "Multiply priority by this factor when dismissed (0.0-1.0)", type: "number", min: 0, max: 1, step: 0.1 },
  ];

  return (
    <div style={{ backgroundColor: "#f9fafb", minHeight: "100vh" }}>
      <div style={{ maxWidth: 800, margin: "0 auto" }}>
        <div style={{ backgroundColor: "white", padding: "32px", borderRadius: "12px", marginBottom: "24px", boxShadow: "0 2px 12px rgba(0,0,0,0.08)" }}>
          <h1 style={{ fontSize: 36, fontWeight: 800, margin: 0, color: "#111827" }}>Recommendation Settings</h1>
          <p style={{ color: "#6b7280", marginTop: 8 }}>Configure thresholds for AI-driven cost recommendations.</p>
        </div>

        {message && (
          <div style={{ padding: 16, borderRadius: 8, marginBottom: 24, background: message.type === "success" ? "#d1fae5" : "#fee2e2", color: message.type === "success" ? "#065f46" : "#991b1b", fontWeight: 600 }}>
            {message.text}
          </div>
        )}

        {loading ? (
          <div style={{ background: "white", padding: 40, borderRadius: 12, textAlign: "center", color: "#6b7280" }}>Loading settings…</div>
        ) : (
          <div style={{ background: "white", padding: 32, borderRadius: 12, boxShadow: "0 2px 12px rgba(0,0,0,0.08)" }}>
            <div style={{ display: "grid", gap: 24 }}>
              {fields.map((field) => (
                <div key={field.key}>
                  <label style={{ display: "block", fontWeight: 700, color: "#111827", marginBottom: 4 }}>
                    {field.label}
                  </label>
                  <p style={{ fontSize: 12, color: "#6b7280", margin: "0 0 8px 0" }}>{field.desc}</p>
                  <input
                    type={field.type}
                    value={settings[field.key] || ""}
                    onChange={(e) => handleChange(field.key, e.target.value)}
                    min={field.min}
                    max={field.max}
                    step={field.step || 1}
                    style={{
                      width: "100%",
                      padding: "10px 12px",
                      borderRadius: 8,
                      border: "2px solid #e5e7eb",
                      fontSize: 14,
                      fontWeight: 600,
                      color: "#111827",
                    }}
                  />
                </div>
              ))}
            </div>

            <div style={{ marginTop: 32, display: "flex", gap: 12 }}>
              <button
                onClick={handleSave}
                disabled={saving}
                style={{
                  padding: "12px 24px",
                  borderRadius: 8,
                  border: "2px solid #3b82f6",
                  background: saving ? "#e5e7eb" : "#3b82f6",
                  color: saving ? "#9ca3af" : "white",
                  fontWeight: 700,
                  cursor: saving ? "not-allowed" : "pointer",
                }}
              >
                {saving ? "Saving…" : "Save Settings"}
              </button>
              <button
                onClick={handleReset}
                disabled={saving}
                style={{
                  padding: "12px 24px",
                  borderRadius: 8,
                  border: "2px solid #e5e7eb",
                  background: "white",
                  color: "#374151",
                  fontWeight: 700,
                  cursor: saving ? "not-allowed" : "pointer",
                }}
              >
                Reset
              </button>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
