export default function PerServiceBudgetTable({ items }) {
  if (!items || items.length === 0) {
    return (
      <div className="mt-8 bg-white rounded-xl shadow p-4">
        <p className="text-gray-500 text-sm">
          No per-service cost data available yet.
        </p>
      </div>
    );
  }

  const statusClasses = {
    good: "bg-green-100 text-green-700",
    warning: "bg-amber-100 text-amber-700",
    danger: "bg-red-100 text-red-700",
    "no-budget": "bg-gray-100 text-gray-600",
  };

  return (
    <div className="mt-8 bg-white rounded-xl shadow p-4">
      <h2 className="text-lg font-semibold mb-4">Per-Service Budgets</h2>
      <div className="overflow-x-auto">
        <table className="min-w-full text-sm">
          <thead className="border-b bg-gray-50">
            <tr>
              <th className="text-left py-2 px-3">Service</th>
              <th className="text-right py-2 px-3">Actual</th>
              <th className="text-right py-2 px-3">Budget</th>
              <th className="text-right py-2 px-3">Projected</th>
              <th className="text-center py-2 px-3">Status</th>
            </tr>
          </thead>
          <tbody>
            {items.map((svc) => (
              <tr key={svc.service} className="border-b last:border-0">
                <td className="py-2 px-3 font-medium text-gray-800">
                  {svc.service}
                </td>
                <td className="py-2 px-3 text-right">
                  ${svc.actual_spend.toFixed(2)}
                </td>
                <td className="py-2 px-3 text-right">
                  {svc.budget != null ? `$${svc.budget.toFixed(2)}` : "—"}
                </td>
                <td className="py-2 px-3 text-right">
                  ${svc.projected_spend.toFixed(2)}
                </td>
                <td className="py-2 px-3 text-center">
                  <span
                    className={
                      "inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-semibold " +
                      statusClasses[svc.status]
                    }
                  >
                    {svc.status === "good" && "On Track"}
                    {svc.status === "warning" && "At Risk"}
                    {svc.status === "danger" && "Over Budget"}
                    {svc.status === "no-budget" && "No Budget Set"}
                  </span>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}
