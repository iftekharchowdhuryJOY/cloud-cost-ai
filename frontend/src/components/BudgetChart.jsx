import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  Tooltip,
  CartesianGrid,
  ResponsiveContainer,
  ReferenceLine,
} from "recharts";

export default function BudgetChart({ data, budget }) {
  /**
   * data = [
   *   { date: "2025-11-01", actual: 2.11, projected: 4.22 },
   *   { date: "2025-11-02", actual: 3.85, projected: 5.30 },
   *   ...
   * ]
   *
   * budget = 100 (monthly budget)
   */

  return (
    <div className="w-full bg-white rounded-xl shadow p-4 h-[350px]">
      <h2 className="text-lg font-semibold mb-4">Budget Overview</h2>

      {/* FIXED HEIGHT so chart becomes visible */}
      <ResponsiveContainer width="100%" height={300}>
        <LineChart data={data}>
          <CartesianGrid strokeDasharray="3 3" opacity={0.4} />

          {/* Date Axis */}
          <XAxis
            dataKey="date"
            tick={{ fontSize: 12 }}
            tickMargin={8}
          />

          {/* Cost Axis */}
          <YAxis
            tick={{ fontSize: 12 }}
            tickMargin={8}
            axisLine={false}
            tickLine={false}
          />

          <Tooltip
            contentStyle={{
              background: "#fff",
              borderRadius: "8px",
              border: "1px solid #eee",
            }}
          />

          {/* Budget Line */}
          <ReferenceLine
            y={budget}
            stroke="#EF4444"
            strokeDasharray="4 4"
            label={{
              value: `Budget ($${budget})`,
              position: "right",
              fill: "#EF4444",
              fontSize: 12,
            }}
          />

          {/* Actual cumulative spend */}
          <Line
            type="monotone"
            dataKey="actual"
            stroke="#3B82F6"
            strokeWidth={2.2}
            dot={false}
            name="Actual Spend"
          />

          {/* Projected spend trend */}
          <Line
            type="monotone"
            dataKey="projected"
            stroke="#A855F7"
            strokeWidth={2}
            strokeDasharray="5 5"
            dot={false}
            name="Projected"
          />
        </LineChart>
      </ResponsiveContainer>
    </div>
  );
}
