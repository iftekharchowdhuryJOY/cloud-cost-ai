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

export default function TotalSpendChart({ data }) {
  // Aggregate total cost per day
  const chartData = useMemo(() => {
    const byDay = {};

    data.forEach((row) => {
      const day = row.day;
      const cost = Number(row.cost) || 0;
      if (!byDay[day]) {
        byDay[day] = 0;
      }
      byDay[day] += cost;
    });

    return Object.entries(byDay)
      .map(([day, total]) => ({ day, total }))
      .sort((a, b) => new Date(a.day) - new Date(b.day));
  }, [data]);

  if (!chartData.length) {
    return (
      <div className="w-full h-64 flex items-center justify-center text-gray-500 text-sm">
        No data available for chart.
      </div>
    );
  }

  return (
    <div className="w-full h-72 bg-white shadow rounded-lg p-4 mb-6">
      <h2 className="text-sm font-semibold text-gray-700 mb-2">
        Total Spend per Day
      </h2>
      <ResponsiveContainer width="100%" height="100%">
        <LineChart data={chartData} margin={{ top: 10, right: 20, left: 0, bottom: 10 }}>
          <CartesianGrid strokeDasharray="3 3" />
          <XAxis
            dataKey="day"
            tick={{ fontSize: 11 }}
            tickMargin={8}
          />
          <YAxis
            tick={{ fontSize: 11 }}
            tickFormatter={(v) => v.toFixed(2)}
          />
          <Tooltip
            formatter={(value) => [`$${Number(value).toFixed(4)}`, "Total"]}
            labelFormatter={(label) => `Date: ${label}`}
          />
          <Line
            type="monotone"
            dataKey="total"
            stroke="#3b82f6" // Tailwind blue-500
            strokeWidth={2}
            dot={false}
            activeDot={{ r: 4 }}
          />
        </LineChart>
      </ResponsiveContainer>
    </div>
  );
}
