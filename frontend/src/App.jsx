import { useState } from "react";
import Dashboard from "./pages/Dashboard";
import ResourceDashboard from "./pages/ResourceDashboard";
import AnomalyDashboard from "./pages/AnomalyDashboard";
import BudgetDashboard from "./pages/BudgetDashboard";
import ServiceBudgets from "./pages/ServiceBudgets";
import RiskHeatmap from "./pages/RiskHeatmap";   // ✅ NEW

function App() {

  const [tab, setTab] = useState("overview");

  return (
    <div className="min-h-screen bg-gray-100">
      {/* Top nav / tabs */}
      <header className="bg-white shadow mb-4">
        <div className="max-w-6xl mx-auto px-6 py-4 flex items-center gap-4">
          <h1 className="text-xl font-bold text-gray-800">
            Cloud Cost AI
          </h1>

          <button
            onClick={() => setTab("overview")}
            className={`px-3 py-1 rounded text-sm ${
              tab === "overview"
                ? "bg-blue-500 text-white"
                : "text-gray-600 hover:bg-gray-100"
            }`}
          >
            Spend Overview
          </button>

          <button
            onClick={() => setTab("resources")}
            className={`px-3 py-1 rounded text-sm ${
              tab === "resources"
                ? "bg-blue-500 text-white"
                : "text-gray-600 hover:bg-gray-100"
            }`}
          >
            Resource-level Costs
          </button>

          <button
            onClick={() => setTab("anomalies")}
            className={`px-3 py-1 rounded text-sm ${
              tab === "anomalies"
                ? "bg-blue-500 text-white"
                : "text-gray-600 hover:bg-gray-100"
            }`}
          >
            Anomalies
          </button>

          <button
            onClick={() => setTab("budgets")}
            className={`px-3 py-1 rounded text-sm ${
              tab === "budgets"
                ? "bg-blue-500 text-white"
                : "text-gray-600 hover:bg-gray-100"
            }`}
          >
            Budgets & Burn
          </button>

          {/* ✅ NEW TAB */}
          <button
            onClick={() => setTab("service-budgets")}
            className={`px-3 py-1 rounded text-sm ${
              tab === "service-budgets"
                ? "bg-blue-500 text-white"
                : "text-gray-600 hover:bg-gray-100"
            }`}
          >
            Service Budgets
          </button>

          {/* ✅ HEATMAP TAB */}
          <button
            onClick={() => setTab("risk-heatmap")}
            className={`px-3 py-1 rounded text-sm ${
              tab === "risk-heatmap"
                ? "bg-blue-500 text-white"
                : "text-gray-600 hover:bg-gray-100"
            }`}
          >
            Risk Heatmap
          </button>

        </div>
      </header>

      {/* Page content */}
      <main className="max-w-6xl mx-auto px-6">
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
        ) : null}
      </main>

    </div>
  );
}

export default App;
