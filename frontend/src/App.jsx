import { useState } from "react";
import Dashboard from "./pages/Dashboard";
import ResourceDashboard from "./pages/ResourceDashboard";
import AnomalyDashboard from "./pages/AnomalyDashboard";
import BudgetDashboard from "./pages/BudgetDashboard";
import ServiceBudgets from "./pages/ServiceBudgets";
import RiskHeatmap from "./pages/RiskHeatmap";
import ServiceTrends from "./pages/ServiceTrends";
import Recommendations from "./pages/Recommendations";
import Settings from "./pages/Settings";
import AiChatbot from "./components/AiChatbot";

function App() {

  const [tab, setTab] = useState("overview");

  const tabs = [
    { id: "overview", label: "Spend Overview" },
    { id: "resources", label: "Resources" },
    { id: "anomalies", label: "Anomalies" },
    { id: "budgets", label: "Budgets" },
    { id: "service-budgets", label: "Service Budgets" },
    { id: "risk-heatmap", label: "Risk Heatmap" },
    { id: "service-trends", label: "Trends" },
    { id: "recommendations", label: "Recommendations" },
    { id: "settings", label: "Settings" },
  ];

  const getTabLabel = (id) => {
    const labels = {
      "overview": "Spend Overview",
      "resources": "Resource-level Costs",
      "anomalies": "Anomalies",
      "budgets": "Budgets & Burn",
      "service-budgets": "Service Budgets",
      "risk-heatmap": "Risk Heatmap",
      "service-trends": "Service Trends",
      "recommendations": "Recommendations",
      "settings": "Settings"
    };
    return labels[id] || "";
  };

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <div className="bg-white border-b border-gray-200 sticky top-0 z-50">
        <div className="px-6 py-4">
          <h1 className="text-3xl font-bold text-gray-900 mb-4">
            Cloud Cost AI
          </h1>
          
          {/* Horizontal scrollable tabs */}
          <div className="flex items-center gap-2 overflow-x-auto pb-2" style={{ scrollbarWidth: 'thin' }}>
            {tabs.map((t) => (
              <button
                key={t.id}
                onClick={() => setTab(t.id)}
                className={`px-4 py-2 rounded-lg text-sm font-medium whitespace-nowrap transition-all ${
                  tab === t.id
                    ? "bg-blue-600 text-white shadow-md"
                    : "bg-gray-100 text-gray-700 hover:bg-gray-200"
                }`}
              >
                {t.label}
              </button>
            ))}
          </div>
        </div>

        {/* Breadcrumb */}
        <div className="px-6 pb-3">
          <div className="flex items-center gap-2 text-sm text-gray-600">
            <span>Home</span>
            <span>›</span>
            <span className="font-semibold text-gray-900">{getTabLabel(tab)}</span>
          </div>
        </div>
      </div>

      {/* Page content */}
      <main className="px-6 py-6">
        {tab === "overview" ? (
          <Dashboard />
        ) : tab === "resources" ? (
          <ResourceDashboard />
        ) : tab === "anomalies" ? (
          <AnomalyDashboard />
        ) : tab === "budgets" ? (
          <BudgetDashboard />
        ) : tab === "service-budgets" ? (
          <ServiceBudgets />
        ) : tab === "risk-heatmap" ? (
          <RiskHeatmap />
        ) : tab === "service-trends" ? (
          <ServiceTrends />
        ) : tab === "recommendations" ? (
          <Recommendations />
        ) : tab === "settings" ? (
          <Settings />
        ) : null}
      </main>
      <AiChatbot />
    </div>
  );
}

export default App;
