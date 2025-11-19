import { useState, useEffect } from "react";
import axios from "axios";
import BudgetChart from "../components/BudgetChart";

// Toggle fake data
const DEV_MODE = true;

// Fake spend to test chart
const fakeDailyData = [
  { date: "2025-11-01", cost: 0.5 },
  { date: "2025-11-02", cost: 0.8 },
  { date: "2025-11-03", cost: 1.2 },
  { date: "2025-11-04", cost: 2.4 },
  { date: "2025-11-05", cost: 3.1 },
  { date: "2025-11-06", cost: 3.9 },
  { date: "2025-11-07", cost: 4.6 },
];

// Build cumulative + projected
function buildChartData(daily, budget) {
  let running = 0;

  return daily.map((row) => {
    running += row.cost;
    return {
      date: row.date,
      actual: running,
      projected: running + 0.5, // simple projection for testing
    };
  });
}

export default function BudgetDashboard() {
  const [budget, setBudget] = useState(10); 
  const [awsChartData, setAwsChartData] = useState([]);

  const fetchFromBackend = async () => {
    if (DEV_MODE) return; // Skip AWS in fake mode

    try {
      const api = import.meta.env.VITE_API_URL;
      const res = await axios.get(`${api}/api/budget`, {
        params: { budget },
      });

      const backend = res.data.data;

      // If backend returns chart points, use them
      if (backend.chart_points) {
        setAwsChartData(backend.chart_points);
      }
    } catch (err) {
      console.error("Budget error", err);
    }
  };

  useEffect(() => {
    fetchFromBackend();
  }, []);

  // Decide which dataset to show
  const finalChartData = DEV_MODE
    ? buildChartData(fakeDailyData, budget)
    : awsChartData;

  return (
    <div className="min-h-screen bg-gray-50 p-8">
      <h1 className="text-3xl font-bold text-gray-800 mb-6">💰 Budget & Burn Rate</h1>

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
          onClick={fetchFromBackend}
          className="px-4 py-2 bg-blue-500 text-white rounded hover:bg-blue-600"
        >
          Update
        </button>

        {DEV_MODE && (
          <span className="text-purple-600 font-semibold ml-2">
            DEV MODE ACTIVE (Fake Data)
          </span>
        )}
      </div>

      {/* Chart */}
      <BudgetChart data={finalChartData} budget={budget} />
    </div>
  );
}
