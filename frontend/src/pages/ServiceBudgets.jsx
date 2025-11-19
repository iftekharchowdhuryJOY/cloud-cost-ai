import { useEffect, useState } from "react";
import axios from "axios";

export default function ServiceBudgets() {
  const [services, setServices] = useState([]);
  const [budgets, setBudgets] = useState({});
  const [loading, setLoading] = useState(true);

  const api = import.meta.env.VITE_API_URL;

  useEffect(() => {
    fetchData();
  }, []);

  const fetchData = async () => {
    setLoading(true);
    try {
      const [budgetsRes, usageRes] = await Promise.all([
        axios.get(`${api}/api/budget/services`),
        axios.get(`${api}/api/budget/services/usage`),
      ]);
      setBudgets(budgetsRes.data.budgets);
      setServices(usageRes.data.services);
    } catch (err) {
      console.error("Error fetching data:", err);
    }
    setLoading(false);
  };

  const updateBudget = async (service, newBudget) => {
    if (!newBudget || Number(newBudget) <= 0) return;
    await axios.post(`${api}/api/budget/services`, {
      service,
      budget: Number(newBudget),
    });
    fetchData();
  };

  const getStatusIndicator = (status) => {
    switch (status) {
      case "danger":
        return "🔴";
      case "warning":
        return "🟡";
      case "good":
        return "🟢";
      default:
        return "⚪";
    }
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center h-screen">
        <p className="text-gray-500">Loading...</p>
      </div>
    );
  }

  return (
    <div style={{ 
      padding: "40px", 
      backgroundColor: "#f9fafb", 
      minHeight: "100vh",
      backgroundImage: "linear-gradient(135deg, #f9fafb 0%, #f3f4f6 100%)"
    }}>
      {/* Header Section with Gradient */}
      <div style={{ 
        display: "flex", 
        justifyContent: "space-between", 
        alignItems: "flex-start", 
        marginBottom: "48px",
        paddingBottom: "24px",
        borderBottom: "2px solid #e5e7eb"
      }}>
        <div>
          <h1 style={{ 
            fontSize: "42px", 
            fontWeight: "800", 
            color: "#1f2937", 
            marginBottom: "8px",
            backgroundImage: "linear-gradient(135deg, #1f2937 0%, #374151 100%)",
            backgroundClip: "text",
            WebkitBackgroundClip: "text",
            WebkitTextFillColor: "transparent",
          }}>
            Service Budget Overview
          </h1>
          <p style={{ 
            color: "#6b7280",
            fontSize: "16px",
            fontWeight: "500"
          }}>
            Monitor and optimize spending across all AWS services
          </p>
        </div>
        <button
          onClick={() => fetchData()}
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
            whiteSpace: "nowrap",
          }}
          onMouseOver={(e) => {
            e.target.style.backgroundColor = "#2563eb";
            e.target.style.boxShadow = "0 8px 20px rgba(59, 130, 246, 0.4)";
            e.target.style.transform = "translateY(-2px)";
          }}
          onMouseOut={(e) => {
            e.target.style.backgroundColor = "#3b82f6";
            e.target.style.boxShadow = "0 4px 15px rgba(59, 130, 246, 0.3)";
            e.target.style.transform = "translateY(0)";
          }}
        >
          🔄 Refresh Data
        </button>
      </div>

      {/* Stats Summary Row */}
      <div
        style={{
          display: "grid",
          gridTemplateColumns: "repeat(3, 1fr)",
          gap: "16px",
          marginBottom: "40px",
          maxWidth: "1400px",
          margin: "0 auto 40px auto",
        }}
      >
        {[
          { label: "Total Services", value: services.length, icon: "📊" },
          { label: "Total Spending", value: `$${services.reduce((sum, s) => sum + s.actual, 0).toFixed(2)}`, icon: "💰" },
          { label: "Total Budget", value: `$${Object.values(budgets).reduce((sum, b) => sum + b, 0).toFixed(2)}`, icon: "🎯" },
        ].map((stat, idx) => (
          <div
            key={idx}
            style={{
              backgroundColor: "white",
              borderRadius: "16px",
              padding: "28px",
              boxShadow: "0 2px 12px rgba(0, 0, 0, 0.06)",
              border: "1px solid #e5e7eb",
              transition: "all 0.3s",
              position: "relative",
              overflow: "hidden",
            }}
            onMouseOver={(e) => {
              e.currentTarget.style.boxShadow = "0 12px 28px rgba(0, 0, 0, 0.12)";
              e.currentTarget.style.transform = "translateY(-6px)";
            }}
            onMouseOut={(e) => {
              e.currentTarget.style.boxShadow = "0 2px 12px rgba(0, 0, 0, 0.06)";
              e.currentTarget.style.transform = "translateY(0)";
            }}
          >
            {/* Gradient overlay effect */}
            <div
              style={{
                position: "absolute",
                top: "0",
                right: "0",
                width: "100px",
                height: "100px",
                background: `radial-gradient(circle, ${
                  idx === 0
                    ? "rgba(59, 130, 246, 0.1)"
                    : idx === 1
                    ? "rgba(16, 185, 129, 0.1)"
                    : "rgba(139, 92, 246, 0.1)"
                }, transparent)`,
                borderRadius: "50%",
              }}
            />
            <div style={{ fontSize: "32px", marginBottom: "12px", position: "relative", zIndex: "1" }}>
              {stat.icon}
            </div>
            <p
              style={{
                fontSize: "12px",
                color: "#9ca3af",
                margin: "0",
                fontWeight: "600",
                textTransform: "uppercase",
                letterSpacing: "0.5px",
              }}
            >
              {stat.label}
            </p>
            <p
              style={{
                fontSize: "32px",
                fontWeight: "800",
                color: idx === 0 ? "#3b82f6" : idx === 1 ? "#10b981" : "#8b5cf6",
                margin: "12px 0 0 0",
              }}
            >
              {stat.value}
            </p>
          </div>
        ))}
      </div>

      {/* Card Grid Container - Centered and properly spaced */}
      <div
        style={{
          display: "grid",
          gridTemplateColumns: "repeat(3, 1fr)",
          gap: "28px",
          maxWidth: "1400px",
          margin: "0 auto",
          width: "100%",
        }}
      >
        {services.map((s) => {
          const budget = budgets[s.service] || 0;
          const utilization = budget > 0 ? Math.round((s.actual / budget) * 100) : 0;
          const isOverBudget = utilization > 100;
          const isWarning = utilization > 80;

          return (
            <div
              key={s.service}
              style={{
                backgroundColor: "white",
                borderRadius: "12px",
                padding: "28px",
                display: "flex",
                flexDirection: "column",
                boxShadow: "0 2px 12px rgba(0, 0, 0, 0.08)",
                transition: "all 0.3s cubic-bezier(0.4, 0, 0.2, 1)",
                border: isOverBudget 
                  ? "2px solid #ef4444" 
                  : isWarning 
                  ? "2px solid #f59e0b"
                  : "2px solid #e5e7eb",
                position: "relative",
                overflow: "hidden",
              }}
              onMouseOver={(e) => {
                e.currentTarget.style.boxShadow = "0 12px 28px rgba(0, 0, 0, 0.15)";
                e.currentTarget.style.transform = "translateY(-6px)";
              }}
              onMouseOut={(e) => {
                e.currentTarget.style.boxShadow = "0 2px 12px rgba(0, 0, 0, 0.08)";
                e.currentTarget.style.transform = "translateY(0)";
              }}
            >
              {/* Gradient top accent */}
              <div
                style={{
                  position: "absolute",
                  top: "0",
                  left: "0",
                  right: "0",
                  height: "4px",
                  background: isOverBudget
                    ? "linear-gradient(90deg, #ef4444, #f87171)"
                    : isWarning
                    ? "linear-gradient(90deg, #f59e0b, #fbbf24)"
                    : "linear-gradient(90deg, #10b981, #34d399)",
                }}
              />

              {/* Status Badge */}
              <div style={{ marginBottom: "16px", display: "flex", alignItems: "center", justifyContent: "space-between" }}>
                <span
                  style={{
                    display: "inline-flex",
                    alignItems: "center",
                    gap: "6px",
                    fontSize: "11px",
                    fontWeight: "700",
                    paddingLeft: "10px",
                    paddingRight: "10px",
                    paddingTop: "4px",
                    paddingBottom: "4px",
                    backgroundColor: isOverBudget
                      ? "#fee2e2"
                      : isWarning
                      ? "#fef3c7"
                      : "#ecfdf5",
                    color: isOverBudget ? "#991b1b" : isWarning ? "#92400e" : "#065f46",
                    borderRadius: "6px",
                    textTransform: "uppercase",
                    letterSpacing: "0.5px",
                  }}
                >
                  {isOverBudget ? "🔴 Over Budget" : isWarning ? "🟡 Warning" : "🟢 Healthy"}
                </span>
              </div>

              {/* Service Name */}
              <h2
                style={{
                  fontSize: "18px",
                  fontWeight: "700",
                  color: "#1f2937",
                  marginBottom: "12px",
                  marginTop: "0",
                }}
              >
                {s.service}
              </h2>

              {/* Spending Data with Visual Hierarchy */}
              <div style={{ marginBottom: "24px" }}>
                <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: "16px", marginBottom: "12px" }}>
                  <div>
                    <p style={{ fontSize: "11px", color: "#6b7280", margin: "0 0 4px 0", fontWeight: "600", textTransform: "uppercase", letterSpacing: "0.5px" }}>
                      Current Spend
                    </p>
                    <p style={{ fontSize: "24px", fontWeight: "800", color: "#1f2937", margin: "0" }}>
                      ${s.actual.toFixed(2)}
                    </p>
                  </div>
                  <div>
                    <p style={{ fontSize: "11px", color: "#6b7280", margin: "0 0 4px 0", fontWeight: "600", textTransform: "uppercase", letterSpacing: "0.5px" }}>
                      Monthly Budget
                    </p>
                    <p style={{ fontSize: "24px", fontWeight: "800", color: "#3b82f6", margin: "0" }}>
                      ${budget.toFixed(2)}
                    </p>
                  </div>
                </div>

                {/* Progress Bar */}
                {budget > 0 && (
                  <div>
                    <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: "8px" }}>
                      <p style={{ fontSize: "12px", color: "#6b7280", margin: "0", fontWeight: "600" }}>
                        Budget Utilization
                      </p>
                      <p style={{ 
                        fontSize: "13px", 
                        fontWeight: "700", 
                        color: isOverBudget ? "#ef4444" : isWarning ? "#f59e0b" : "#10b981",
                        margin: "0"
                      }}>
                        {utilization}%
                      </p>
                    </div>
                    <div
                      style={{
                        width: "100%",
                        height: "8px",
                        backgroundColor: "#e5e7eb",
                        borderRadius: "9999px",
                        overflow: "hidden",
                      }}
                    >
                      <div
                        style={{
                          height: "100%",
                          width: `${Math.min(utilization, 100)}%`,
                          background: isOverBudget
                            ? "linear-gradient(90deg, #ef4444, #f87171)"
                            : isWarning
                            ? "linear-gradient(90deg, #f59e0b, #fbbf24)"
                            : "linear-gradient(90deg, #10b981, #34d399)",
                          transition: "width 0.5s ease",
                          borderRadius: "9999px",
                        }}
                      />
                    </div>
                  </div>
                )}
              </div>

              {/* Input and Action Buttons */}
              <div
                style={{
                  display: "flex",
                  alignItems: "center",
                  gap: "12px",
                  marginTop: "auto",
                  paddingTop: "16px",
                  borderTop: "1px solid #e5e7eb",
                }}
              >
                <input
                  type="number"
                  step="0.01"
                  defaultValue={budget}
                  placeholder="Set budget"
                  style={{
                    flex: 1,
                    borderTop: "none",
                    borderLeft: "none",
                    borderRight: "none",
                    borderBottom: "2px solid #d1d5db",
                    backgroundColor: "transparent",
                    padding: "10px 0",
                    fontSize: "14px",
                    fontWeight: "600",
                    outline: "none",
                    fontFamily: "inherit",
                    transition: "border-color 0.2s",
                  }}
                  onFocus={(e) => {
                    e.target.style.borderBottomColor = "#3b82f6";
                  }}
                  onBlur={(e) => {
                    e.target.style.borderBottomColor = "#d1d5db";
                    const newVal = e.target.value;
                    if (newVal && newVal !== budget.toString()) {
                      updateBudget(s.service, newVal);
                    }
                  }}
                />
                <button
                  style={{
                    background: "none",
                    border: "none",
                    cursor: "pointer",
                    fontSize: "18px",
                    color: "#9ca3af",
                    transition: "all 0.2s",
                    padding: "6px",
                    display: "flex",
                    alignItems: "center",
                    justifyContent: "center",
                  }}
                  onMouseOver={(e) => {
                    e.target.style.color = "#3b82f6";
                    e.target.style.transform = "scale(1.2)";
                  }}
                  onMouseOut={(e) => {
                    e.target.style.color = "#9ca3af";
                    e.target.style.transform = "scale(1)";
                  }}
                >
                  →
                </button>
                <button
                  style={{
                    background: "none",
                    border: "none",
                    cursor: "pointer",
                    fontSize: "18px",
                    color: "#9ca3af",
                    transition: "all 0.2s",
                    padding: "6px",
                    display: "flex",
                    alignItems: "center",
                    justifyContent: "center",
                  }}
                  onMouseOver={(e) => {
                    e.target.style.color = "#10b981";
                    e.target.style.transform = "scale(1.2)";
                  }}
                  onMouseOut={(e) => {
                    e.target.style.color = "#9ca3af";
                    e.target.style.transform = "scale(1)";
                  }}
                >
                  +
                </button>
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
}
