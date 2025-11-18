import { useMemo } from "react";
import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  Tooltip,
  CartesianGrid,
  ResponsiveContainer,
  Legend,
} from "recharts";

export default function TopServicesChart({ data }) {
  // 1. Determine total spend per service
  const serviceTotals = useMemo(() => {
    const totals = {};
    data.forEach((row) => {
      const svc = row.service;
      const cost = Number(row.cost) || 0;
      if (!totals[svc]) totals[svc] = 0;
      totals[svc] += cost;
    });
    return totals;
  }, [data]);

  // 2. Identify Top 3 spenders
  const top3 = useMemo(() => {
    return Object.entries(serviceTotals)
      .sort((a, b) => b[1] - a[1]) // descending
      .slice(0, 3)
      .map(([svc]) => svc);
  }, [serviceTotals]);

  // 3. Build dataset: { day, S3: 0.12, EC2: 2.31, ... }
  const chartData = useMemo(() => {
    const grouped = {};

    data.forEach((row) => {
      const { day, service, cost } = row;
      if (!top3.includes(service)) return; // keep only top 3

      if (!grouped[day]) grouped[day] = { day };
      grouped[day][service] = Number(cost) || 0;
    });

    return Object.values(grouped).sort(
      (a, b) => new Date(a.day) - new Date(b.day)
    );
  }, [data, top3]);

  // 4. If no chartable data
  if (!chartData.length || top3.length === 0) {
    return (
      <div className="w-full h-72 bg-white shadow rounded-lg flex items-center justify-center text-gray-500 text-sm mt-8">
        Not enough spend data to show Top 3 Services.
      </div>
    );
  }

  // 5. Service → color map
  const colors = ["#3b82f6", "#10b981", "#f97316"]; // blue, green, orange

  return (
    <div className="w-full h-80 bg-white shadow rounded-lg p-4 mb-6 mt-8">
      <h2 className="text-sm font-semibold text-gray-700 mb-3">
        Top 3 Services – Daily Spend Trends
      </h2>

      <ResponsiveContainer width="100%" height="100%">
        <LineChart data={chartData} margin={{ top: 10, right: 20, left: 0, bottom: 10 }}>
          <CartesianGrid strokeDasharray="3 3" />
          <XAxis dataKey="day" tick={{ fontSize: 11 }} tickMargin={8} />
          <YAxis tick={{ fontSize: 11 }} tickFormatter={(v) => v.toFixed(2)} />
          <Tooltip formatter={(v) => `$${v.toFixed(6)}`} />
          <Legend />

          {top3.map((svc, idx) => (
            <Line
              key={svc}
              type="monotone"
              dataKey={svc}
              stroke={colors[idx]}
              strokeWidth={2}
              dot={{ r: 3 }}
              activeDot={{ r: 5 }}
            />
          ))}
        </LineChart>
      </ResponsiveContainer>
    </div>
  );
}
