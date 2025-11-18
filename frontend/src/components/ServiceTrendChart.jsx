import { useMemo } from "react";
import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  Tooltip,
  CartesianGrid,
  ResponsiveContainer,
} from "recharts";

export default function ServiceTrendChart({ data, selectedService }) {
  // If no service selected, show a placeholder
  if (!selectedService) {
    return (
      <div className="w-full h-72 bg-white shadow rounded-lg flex items-center justify-center text-gray-500 text-sm mt-8">
        Select a service to view its trend.
      </div>
    );
  }

  // Build daily cost for the selected service
  const chartData = useMemo(() => {
    const grouped = {};

    data.forEach((row) => {
      if (row.service !== selectedService) return;

      const { day, cost } = row;

      if (!grouped[day]) grouped[day] = { day, cost: 0 };
      grouped[day].cost += Number(cost) || 0;
    });

    return Object.values(grouped).sort(
      (a, b) => new Date(a.day) - new Date(b.day)
    );
  }, [data, selectedService]);

  // If no data for that service
  if (!chartData.length) {
    return (
      <div className="w-full h-72 bg-white shadow rounded-lg flex items-center justify-center text-gray-500 text-sm mt-8">
        No cost found for {selectedService}.
      </div>
    );
  }

  // Check if all values are zero
  const allZero = chartData.every((p) => p.cost === 0);

  if (allZero) {
    return (
      <div className="w-full h-72 bg-white shadow rounded-lg flex items-center justify-center text-gray-500 text-sm mt-8">
        {selectedService} has zero cost in this range.
      </div>
    );
  }

  // Chart
  return (
    <div className="w-full h-80 bg-white shadow rounded-lg p-4 mb-6 mt-8">
      <h2 className="text-sm font-semibold text-gray-700 mb-3">
        {selectedService} – Daily Spend Trend
      </h2>

      <ResponsiveContainer width="100%" height="100%">
        <LineChart
          data={chartData}
          margin={{ top: 10, right: 20, left: 0, bottom: 10 }}
        >
          <CartesianGrid strokeDasharray="3 3" />
          <XAxis dataKey="day" tick={{ fontSize: 11 }} tickMargin={8} />
          <YAxis tickFormatter={(v) => v.toFixed(3)} />
          <Tooltip formatter={(v) => `$${v.toFixed(6)}`} />
          <Line
            type="monotone"
            dataKey="cost"
            stroke="#8b5cf6" // purple
            strokeWidth={2}
            dot={{ r: 3 }}
            activeDot={{ r: 5 }}
          />
        </LineChart>
      </ResponsiveContainer>
    </div>
  );
}
