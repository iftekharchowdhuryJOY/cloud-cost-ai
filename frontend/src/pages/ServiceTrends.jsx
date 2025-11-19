import { useEffect, useState } from "react";
import axios from "axios";
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer, ReferenceLine } from "recharts";

export default function ServiceTrends() {
  const [services, setServices] = useState([]);
  const [selectedService, setSelectedService] = useState("");
  const [trendData, setTrendData] = useState([]);
  const [summary, setSummary] = useState(null);
  const [loading, setLoading] = useState(false);
  const [days, setDays] = useState(90);

  const api = import.meta.env.VITE_API_URL;

  // Fetch available services on mount
  useEffect(() => {
    fetchServices();
  }, [days]);

  // Fetch trend when service selected
  useEffect(() => {
    if (selectedService) {
      fetchTrend();
    }
  }, [selectedService, days]);

  const fetchServices = async () => {
    try {
      const res = await axios.get(`${api}/api/costs/services`, {
        params: { days },
      });
      setServices(res.data.services || []);
      if (res.data.services?.length > 0 && !selectedService) {
        setSelectedService(res.data.services[0]);
      }
    } catch (err) {
      console.error("Error fetching services:", err);
    }
  };

  const fetchTrend = async () => {
    if (!selectedService) return;
    
    setLoading(true);
    try {
      const res = await axios.get(`${api}/api/costs/service/${encodeURIComponent(selectedService)}/trend`, {
        params: { days },
      });
      setTrendData(res.data.data || []);
      setSummary(res.data.summary || null);
    } catch (err) {
      console.error("Error fetching trend:", err);
    }
    setLoading(false);
  };

  const getTrendIcon = (trend) => {
    switch (trend) {
      case "increasing":
        return "📈";
      case "decreasing":
        return "📉";
      default:
        return "➡️";
    }
  };

  const getTrendColor = (trend) => {
    switch (trend) {
      case "increasing":
        return "#ef4444";
      case "decreasing":
        return "#10b981";
      default:
        return "#6b7280";
    }
  };

  const anomalyDot = (props) => {
    const { cx, cy, payload } = props;
    if (payload?.is_anomaly) {
      return (
        <circle cx={cx} cy={cy} r={6} stroke="#dc2626" strokeWidth={2} fill="#dc2626" />
      );
    }
    return <circle cx={cx} cy={cy} r={4} fill="#3b82f6" />;
  };

  return (
    <div
      style={{
        padding: "40px",
        backgroundColor: "#f9fafb",
        minHeight: "100vh",
        backgroundImage: "linear-gradient(135deg, #f9fafb 0%, #f3f4f6 100%)",
      }}
    >
      {/* Header */}
      <div
        style={{
          backgroundColor: "white",
          borderRadius: "12px",
          padding: "40px",
          marginBottom: "32px",
          boxShadow: "0 2px 12px rgba(0, 0, 0, 0.08)",
        }}
      >
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
          Service Spend Trends
        </h1>
        <p style={{ color: "#6b7280", fontSize: "16px", fontWeight: "500", margin: "0" }}>
          Track daily spending patterns for individual AWS services
        </p>
      </div>

      {/* Controls */}
      <div
        style={{
          backgroundColor: "white",
          borderRadius: "12px",
          padding: "24px",
          marginBottom: "32px",
          boxShadow: "0 2px 8px rgba(0, 0, 0, 0.06)",
          display: "flex",
          gap: "24px",
          alignItems: "center",
          flexWrap: "wrap",
        }}
      >
        <div style={{ flex: "1 1 300px" }}>
          <label style={{ display: "block", fontWeight: "600", color: "#374151", marginBottom: "8px" }}>
            Select Service:
          </label>
          <select
            value={selectedService}
            onChange={(e) => setSelectedService(e.target.value)}
            style={{
              width: "100%",
              padding: "12px 16px",
              border: "2px solid #e5e7eb",
              borderRadius: "8px",
              fontSize: "14px",
              fontWeight: "500",
              cursor: "pointer",
              backgroundColor: "white",
            }}
          >
            {services.map((svc) => (
              <option key={svc} value={svc}>
                {svc}
              </option>
            ))}
          </select>
        </div>

        <div>
          <label style={{ display: "block", fontWeight: "600", color: "#374151", marginBottom: "8px" }}>
            Time Range:
          </label>
          <div style={{ display: "flex", gap: "8px" }}>
            {[
              { label: "7 Days", value: 7 },
              { label: "30 Days", value: 30 },
              { label: "90 Days", value: 90 },
            ].map((option) => (
              <button
                key={option.value}
                onClick={() => setDays(option.value)}
                style={{
                  padding: "10px 20px",
                  border: days === option.value ? "2px solid #3b82f6" : "2px solid #e5e7eb",
                  borderRadius: "8px",
                  backgroundColor: days === option.value ? "#eff6ff" : "white",
                  color: days === option.value ? "#3b82f6" : "#6b7280",
                  fontWeight: "600",
                  fontSize: "14px",
                  cursor: "pointer",
                  transition: "all 0.2s",
                }}
              >
                {option.label}
              </button>
            ))}
          </div>
        </div>
      </div>

      {/* Summary Stats */}
      {summary && (
        <div
          style={{
            display: "grid",
            gridTemplateColumns: "repeat(auto-fit, minmax(200px, 1fr))",
            gap: "16px",
            marginBottom: "32px",
          }}
        >
          {[
            { label: "Total Spend", value: `$${summary.total_spend}`, icon: "💰", color: "#3b82f6" },
            { label: "Avg Daily", value: `$${summary.avg_daily_spend}`, icon: "📊", color: "#8b5cf6" },
            { label: "Min Daily", value: `$${summary.min_daily}`, icon: "⬇️", color: "#10b981" },
            { label: "Max Daily", value: `$${summary.max_daily}`, icon: "⬆️", color: "#ef4444" },
            {
              label: "Trend",
              value: summary.trend.charAt(0).toUpperCase() + summary.trend.slice(1),
              icon: getTrendIcon(summary.trend),
              color: getTrendColor(summary.trend),
            },
            { label: `MA (${summary.moving_avg_window}d)`, value: "Smoothing", icon: "🧮", color: "#6366f1" },
            { label: "Anomaly Days", value: summary.anomaly_days, icon: "🚨", color: summary.anomaly_days > 0 ? "#dc2626" : "#10b981" },
            ...(summary.budget ? [{ label: "Budget", value: `$${summary.budget}`, icon: "🎯", color: "#f59e0b" }] : []),
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
              <p style={{ fontSize: "11px", color: "#6b7280", margin: "0", fontWeight: "600" }}>{stat.label}</p>
              <p
                style={{
                  fontSize: "24px",
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

      {/* Chart */}
      <div
        style={{
          backgroundColor: "white",
          borderRadius: "12px",
          padding: "32px",
          boxShadow: "0 2px 12px rgba(0, 0, 0, 0.08)",
        }}
      >
        {loading ? (
          <div style={{ textAlign: "center", padding: "60px", color: "#6b7280" }}>
            <p style={{ fontSize: "16px" }}>Loading trend data...</p>
          </div>
        ) : trendData.length === 0 ? (
          <div style={{ textAlign: "center", padding: "60px", color: "#6b7280" }}>
            <p style={{ fontSize: "16px" }}>No data available for this service</p>
          </div>
        ) : (
          <>
            <h2 style={{ fontSize: "20px", fontWeight: "700", color: "#1f2937", marginBottom: "24px" }}>
              Daily Spend: {selectedService}
            </h2>
            <ResponsiveContainer width="100%" height={400}>
              <LineChart data={trendData} margin={{ top: 5, right: 30, left: 20, bottom: 5 }}>
                <CartesianGrid strokeDasharray="3 3" stroke="#e5e7eb" />
                <XAxis
                  dataKey="date"
                  stroke="#6b7280"
                  style={{ fontSize: "12px", fontWeight: "500" }}
                  tickFormatter={(date) => new Date(date).toLocaleDateString("en-US", { month: "short", day: "numeric" })}
                />
                <YAxis
                  stroke="#6b7280"
                  style={{ fontSize: "12px", fontWeight: "500" }}
                  tickFormatter={(value) => `$${value.toFixed(2)}`}
                />
                <Tooltip
                  contentStyle={{
                    backgroundColor: "white",
                    border: "2px solid #e5e7eb",
                    borderRadius: "8px",
                    padding: "12px",
                    boxShadow: "0 4px 12px rgba(0, 0, 0, 0.1)",
                  }}
                  labelFormatter={(date) => new Date(date).toLocaleDateString("en-US", { 
                    year: "numeric",
                    month: "long", 
                    day: "numeric" 
                  })}
                  formatter={(value, name, props) => {
                    if (name === "Daily Cost") return [`$${value.toFixed(2)}`, name];
                    if (name === "Moving Avg") return [`$${value.toFixed(2)}`, name];
                    return [value, name];
                  }}
                />
                <Legend wrapperStyle={{ fontSize: "14px", fontWeight: "600" }} />
                {summary?.budget && (
                  <ReferenceLine y={summary.budget} stroke="#f59e0b" strokeDasharray="4 4" label={{ value: `Budget $${summary.budget}`, position: "right", fill: "#f59e0b", fontSize: 12 }} />
                )}
                <Line
                  type="monotone"
                  dataKey="cost"
                  stroke="#3b82f6"
                  strokeWidth={3}
                  dot={anomalyDot}
                  activeDot={{ r: 6 }}
                  name="Daily Cost"
                />
                <Line
                  type="monotone"
                  dataKey="moving_avg"
                  stroke="#6366f1"
                  strokeWidth={2}
                  strokeDasharray="5 5"
                  dot={false}
                  name="Moving Avg"
                />
              </LineChart>
            </ResponsiveContainer>
          </>
        )}
      </div>
    </div>
  );
}
