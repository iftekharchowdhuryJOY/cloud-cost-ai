import { useState, useEffect } from "react";
import axios from "axios";

export default function BudgetDashboard() {
  const [budget, setBudget] = useState(10); // default $10
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(false);

  const fetchBudgetData = async () => {
    setLoading(true);

    const api = import.meta.env.VITE_API_URL;

    try {
      const res = await axios.get(`${api}/api/budget`, {
        params: { budget },
      });
      setData(res.data);
    } catch (e) {
      console.error("Budget fetch error:", e);
    }

    setLoading(false);
  };

  useEffect(() => {
    fetchBudgetData();
  }, []);

  const statusColors = {
    good: "text-green-600",
    warning: "text-amber-600",
    danger: "text-red-600",
    "no-data": "text-gray-500"
  };

  return (
    <div className="min-h-screen bg-gray-50 p-8">
      <h1 className="text-3xl font-bold text-gray-800 mb-6">
        💰 Budget & Burn Rate
      </h1>

      {/* Budget Input */}
      <div className="flex items-center gap-4 mb-6">
        <label className="text-gray-600">Monthly Budget ($)</label>
        <input
          type="number"
          className="border px-3 py-2 rounded w-28"
          value={budget}
          onChange={(e) => setBudget(Number(e.target.value))}
        />

        <button
          onClick={fetchBudgetData}
          className="px-4 py-2 bg-blue-500 text-white rounded hover:bg-blue-600"
        >
          Update
        </button>
      </div>

      {/* Results */}
      {loading ? (
        <p className="text-gray-400">Calculating…</p>
      ) : data ? (
        <div className="bg-white shadow rounded-lg p-6">
          <div className="flex flex-col gap-3 text-lg">
            <p>
              <strong>Actual Spend:</strong> ${data.actual_spend}
            </p>
            <p>
              <strong>Daily Burn Rate:</strong> ${data.burn_rate}
            </p>
            <p>
              <strong>Projected End-of-Month Spend:</strong>{" "}
              <span
                className={`font-semibold ${statusColors[data.status]}`}
              >
                ${data.projected_spend}
              </span>
            </p>

            <p className={`mt-2 text-xl font-bold ${statusColors[data.status]}`}>
              {data.status === "good" && "🟢 On Track"}
              {data.status === "warning" && "🟡 At Risk"}
              {data.status === "danger" && "🔴 Over Budget"}
              {data.status === "no-data" && "No cost data available"}
            </p>
          </div>
        </div>
      ) : null}
    </div>
  );
}
