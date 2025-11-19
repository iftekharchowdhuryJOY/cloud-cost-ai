import { useEffect, useState } from "react";
import axios from "axios";

export default function RiskHeatmap() {
  const [heatmapData, setHeatmapData] = useState([]);
  const [summary, setSummary] = useState(null);
  const [loading, setLoading] = useState(true);
  const [sortBy, setSortBy] = useState("risk_score");
  const [filterRisk, setFilterRisk] = useState("all");

  const api = import.meta.env.VITE_API_URL;

  useEffect(() => {
    fetchHeatmap();
  }, []);

  const fetchHeatmap = async () => {
    setLoading(true);
    try {
      const res = await axios.get(`${api}/api/budget/risk-heatmap`, {
        params: { days: 30 },
      });
      setHeatmapData(res.data.heatmap);
      setSummary(res.data.summary);
    } catch (err) {
      console.error("Error fetching heatmap:", err);
    }
    setLoading(false);
  };

  // Apply sorting
  const sortedData = [...heatmapData].sort((a, b) => {
    if (sortBy === "risk_score") return b.risk_score - a.risk_score;
    if (sortBy === "utilization_pct") return b.utilization_pct - a.utilization_pct;
    if (sortBy === "service") return a.service.localeCompare(b.service);
    return 0;
  });

  // Apply filtering
  const filteredData =
    filterRisk === "all"
      ? sortedData
      : sortedData.filter((s) => s.risk_level === filterRisk);

  // Determine cell color based on risk
  const getRiskColor = (level) => {
    switch (level) {
      case "danger":
        return "#ef4444";
      case "warning":
        return "#f59e0b";
      case "good":
        return "#10b981";
      default:
        return "#d1d5db";
    }
  };

  const getRiskBgColor = (level) => {
    switch (level) {
      case "danger":
        return "#fee2e2";
      case "warning":
        return "#fef3c7";
      case "good":
        return "#ecfdf5";
      default:
        return "#f3f4f6";
    }
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center h-screen">
        <p className="text-gray-500">Loading risk heatmap...</p>
      </div>
    );
  }

  return (
    <div
      style={{
        padding: "40px",
        backgroundColor: "#f9fafb",
        minHeight: "100vh",
        backgroundImage: "linear-gradient(135deg, #f9fafb 0%, #f3f4f6 100%)",
      }}
    >
      {/* Header - Full width with centered content */}
      <div
        style={{
          backgroundColor: "white",
          borderBottom: "1px solid #e5e7eb",
          padding: "40px",
        }}
      >
        <div
          style={{
            display: "flex",
            justifyContent: "space-between",
            alignItems: "flex-start",
          }}
        >
          <div>
            <h1
              style={{
                fontSize: "42px",
                fontWeight: "800",
                color: "#1f2937",
                marginBottom: "8px",
                backgroundImage: "linear-gradient(135deg, #1f2937 0%, #374151 100%)",
                backgroundClip: "text",
                WebkitBackgroundClip: "text",
                WebkitTextFillColor: "transparent",
              }}
            >
              Risk Heatmap Dashboard
            </h1>
            <p style={{ color: "#6b7280", fontSize: "16px", fontWeight: "500", margin: "0" }}>
              Service risk visualization with real-time metrics
            </p>
          </div>
          <button
            onClick={fetchHeatmap}
            style={{
              paddingLeft: "28px",
              paddingRight: "28px",
              paddingTop: "12px",
              paddingBottom: "12px",
              backgroundColor: "#3b82f6",
              color: "white",
              fontWeight: "700",
              fontSize: "14px",
              borderRadius: "8px",
              border: "none",
              cursor: "pointer",
              transition: "all 0.3s",
              boxShadow: "0 4px 15px rgba(59, 130, 246, 0.3)",
            }}
            onMouseOver={(e) => {
              e.target.style.backgroundColor = "#2563eb";
              e.target.style.transform = "translateY(-2px)";
            }}
            onMouseOut={(e) => {
              e.target.style.backgroundColor = "#3b82f6";
              e.target.style.transform = "translateY(0)";
            }}
          >
            🔄 Refresh
          </button>
        </div>
      </div>

      {/* Summary Stats */}
      <div style={{ padding: "0 40px" }}>
      {summary && (
        <div
          style={{
            display: "grid",
            gridTemplateColumns: "repeat(5, 1fr)",
            gap: "16px",
            marginBottom: "40px",
          }}
        >
          {[
            { label: "Total Services", value: summary.total_services, icon: "📊", color: "#3b82f6" },
            { label: "🔴 Danger", value: summary.danger_count, icon: "🔴", color: "#ef4444" },
            { label: "🟡 Warning", value: summary.warning_count, icon: "🟡", color: "#f59e0b" },
            { label: "🟢 Good", value: summary.good_count, icon: "🟢", color: "#10b981" },
            { label: "Avg Risk Score", value: summary.avg_risk_score, icon: "📈", color: "#8b5cf6" },
          ].map((stat, idx) => (
            <div
              key={idx}
              style={{
                backgroundColor: "white",
                borderRadius: "12px",
                padding: "20px",
                boxShadow: "0 2px 12px rgba(0, 0, 0, 0.08)",
                border: `2px solid ${stat.color}20`,
                textAlign: "center",
              }}
            >
              <p style={{ fontSize: "24px", margin: "0 0 8px 0" }}>{stat.icon}</p>
              <p style={{ fontSize: "11px", color: "#6b7280", margin: "0", fontWeight: "600" }}>
                {stat.label}
              </p>
              <p
                style={{
                  fontSize: "28px",
                  fontWeight: "800",
                  color: stat.color,
                  margin: "8px 0 0 0",
                }}
              >
                {stat.value}
              </p>
            </div>
          ))}
        </div>
      )}

      </div>

      {/* Filters & Sort */}
      <div style={{ padding: "0 40px", marginBottom: "24px" }}>
      <div
        style={{
          display: "flex",
          gap: "16px",
          alignItems: "center",
          backgroundColor: "white",
          padding: "16px 20px",
          borderRadius: "12px",
          boxShadow: "0 2px 8px rgba(0, 0, 0, 0.06)",
        }}
      >
        <label style={{ fontWeight: "600", color: "#374151" }}>Filter:</label>
        <select
          value={filterRisk}
          onChange={(e) => setFilterRisk(e.target.value)}
          style={{
            padding: "8px 12px",
            border: "1px solid #d1d5db",
            borderRadius: "6px",
            fontSize: "14px",
            cursor: "pointer",
            fontWeight: "500",
          }}
        >
          <option value="all">All Services</option>
          <option value="danger">🔴 Danger Only</option>
          <option value="warning">🟡 Warning Only</option>
          <option value="good">🟢 Good Only</option>
        </select>

        <label style={{ fontWeight: "600", color: "#374151", marginLeft: "24px" }}>Sort by:</label>
        <select
          value={sortBy}
          onChange={(e) => setSortBy(e.target.value)}
          style={{
            padding: "8px 12px",
            border: "1px solid #d1d5db",
            borderRadius: "6px",
            fontSize: "14px",
            cursor: "pointer",
            fontWeight: "500",
          }}
        >
          <option value="risk_score">Risk Score (High to Low)</option>
          <option value="utilization_pct">Utilization % (High to Low)</option>
          <option value="service">Service Name (A-Z)</option>
        </select>

        <div style={{ marginLeft: "auto", fontSize: "12px", color: "#6b7280" }}>
          Showing {filteredData.length} of {heatmapData.length} services
        </div>
      </div>
      </div>

      {/* Heatmap Grid */}
      <div style={{ padding: "0 40px 40px 40px" }}>
      {filteredData.length === 0 ? (
        <div
          style={{
            backgroundColor: "white",
            borderRadius: "12px",
            padding: "60px",
            textAlign: "center",
            color: "#6b7280",
          }}
        >
          <p style={{ fontSize: "16px", margin: "0" }}>No services match your filter.</p>
        </div>
      ) : (
        <div
          style={{
            display: "grid",
            gridTemplateColumns: "repeat(3, 1fr)",
            gap: "24px",
          }}
        >
          {filteredData.map((service, idx) => (
            <div
              key={idx}
              style={{
                backgroundColor: getRiskBgColor(service.risk_level),
                border: `2px solid ${getRiskColor(service.risk_level)}`,
                borderRadius: "12px",
                padding: "20px",
                transition: "all 0.3s",
                cursor: "pointer",
                position: "relative",
                overflow: "hidden",
              }}
              onMouseOver={(e) => {
                e.currentTarget.style.transform = "translateY(-4px)";
                e.currentTarget.style.boxShadow = `0 12px 24px ${getRiskColor(service.risk_level)}40`;
              }}
              onMouseOut={(e) => {
                e.currentTarget.style.transform = "translateY(0)";
                e.currentTarget.style.boxShadow = "none";
              }}
            >
              {/* Top accent bar */}
              <div
                style={{
                  position: "absolute",
                  top: "0",
                  left: "0",
                  right: "0",
                  height: "4px",
                  backgroundColor: getRiskColor(service.risk_level),
                }}
              />

              {/* Service name + status icon */}
              <div style={{ display: "flex", justifyContent: "space-between", alignItems: "start", marginBottom: "12px" }}>
                <h3 style={{ fontSize: "16px", fontWeight: "700", margin: "0", color: "#1f2937", flex: 1 }}>
                  {service.service}
                </h3>
                <span style={{ fontSize: "24px" }}>{service.status_icon}</span>
              </div>

              {/* Risk Level Badge */}
              <div
                style={{
                  display: "inline-block",
                  paddingLeft: "10px",
                  paddingRight: "10px",
                  paddingTop: "4px",
                  paddingBottom: "4px",
                  backgroundColor: getRiskColor(service.risk_level),
                  color: "white",
                  fontSize: "11px",
                  fontWeight: "700",
                  borderRadius: "4px",
                  marginBottom: "12px",
                  textTransform: "uppercase",
                  letterSpacing: "0.5px",
                }}
              >
                {service.risk_level === "danger"
                  ? "🔴 CRITICAL"
                  : service.risk_level === "warning"
                  ? "🟡 WARNING"
                  : "🟢 HEALTHY"}
              </div>

              {/* Risk Score - Big Number */}
              <div
                style={{
                  fontSize: "36px",
                  fontWeight: "800",
                  color: getRiskColor(service.risk_level),
                  marginBottom: "16px",
                }}
              >
                {service.risk_score}
                <span style={{ fontSize: "14px", color: "#6b7280", marginLeft: "4px" }}>/100</span>
              </div>

              {/* Metrics Grid */}
              <div
                style={{
                  display: "grid",
                  gridTemplateColumns: "1fr 1fr",
                  gap: "12px",
                  marginBottom: "12px",
                  paddingBottom: "12px",
                  borderBottom: "1px solid #e5e7eb",
                }}
              >
                <div>
                  <p style={{ fontSize: "11px", color: "#6b7280", margin: "0", fontWeight: "600" }}>
                    UTILIZATION
                  </p>
                  <p style={{ fontSize: "18px", fontWeight: "800", margin: "4px 0 0 0", color: "#1f2937" }}>
                    {service.utilization_pct}%
                  </p>
                </div>
                <div>
                  <p style={{ fontSize: "11px", color: "#6b7280", margin: "0", fontWeight: "600" }}>
                    DAILY BURN
                  </p>
                  <p style={{ fontSize: "18px", fontWeight: "800", margin: "4px 0 0 0", color: "#1f2937" }}>
                    ${service.daily_burn.toFixed(3)}
                  </p>
                </div>
                <div>
                  <p style={{ fontSize: "11px", color: "#6b7280", margin: "0", fontWeight: "600" }}>
                    ACTUAL
                  </p>
                  <p style={{ fontSize: "18px", fontWeight: "800", margin: "4px 0 0 0", color: "#1f2937" }}>
                    ${service.actual_spend.toFixed(2)}
                  </p>
                </div>
                <div>
                  <p style={{ fontSize: "11px", color: "#6b7280", margin: "0", fontWeight: "600" }}>
                    BUDGET
                  </p>
                  <p
                    style={{
                      fontSize: "18px",
                      fontWeight: "800",
                      margin: "4px 0 0 0",
                      color: service.budget ? "#1f2937" : "#9ca3af",
                    }}
                  >
                    {service.budget ? `$${service.budget.toFixed(2)}` : "—"}
                  </p>
                </div>
              </div>

              {/* Projection Info */}
              <div style={{ fontSize: "13px", color: "#4b5563", lineHeight: "1.6" }}>
                <p style={{ margin: "0" }}>
                  <strong>Projected:</strong> ${service.projected_spend.toFixed(2)}
                </p>
                <p style={{ margin: "4px 0 0 0" }}>
                  <strong>Days Left:</strong> {service.days_remaining}
                </p>
                {service.estimated_overspend > 0 && (
                  <p style={{ margin: "4px 0 0 0", color: "#ef4444", fontWeight: "600" }}>
                    ⚠️ Over: ${service.estimated_overspend.toFixed(2)}
                  </p>
                )}
              </div>
            </div>
          ))}
        </div>
      )}
      </div>
    </div>
  );
}
