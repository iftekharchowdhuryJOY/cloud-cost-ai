import { useEffect, useState } from "react";
import { DateRange } from "react-date-range";
import { format } from "date-fns";
import { getResourceCosts } from "../api/resourceService";

import "react-date-range/dist/styles.css";
import "react-date-range/dist/theme/default.css";

export default function ResourceDashboard() {
  const [data, setData] = useState([]);
  const [apiMessage, setApiMessage] = useState("");
  const [loading, setLoading] = useState(false);
  const [showPicker, setShowPicker] = useState(false);

  const [selectedService, setSelectedService] = useState("");

  const [range, setRange] = useState([
    {
      startDate: new Date(new Date().setDate(new Date().getDate() - 7)),
      endDate: new Date(),
      key: "selection",
    },
  ]);

  const fetchResources = async () => {
    setLoading(true);

    const start = format(range[0].startDate, "yyyy-MM-dd");
    const end = format(range[0].endDate, "yyyy-MM-dd");

    const res = await getResourceCosts(start, end, selectedService);
    setData(res.data || []);
    setApiMessage(res.message || "");
    setLoading(false);
  };

  useEffect(() => {
    fetchResources();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  const uniqueServices = [...new Set(data.map((row) => row.service))];

  return (
    <div className="min-h-screen bg-gray-50 p-8">
      <h1 className="text-3xl font-bold text-gray-800 mb-6">
        🔍 Resource-level Spend
      </h1>

      {/* Controls */}
      <div className="flex flex-wrap items-center gap-4 mb-6">
        <button
          onClick={() => setShowPicker(!showPicker)}
          className="px-4 py-2 bg-blue-500 text-white rounded hover:bg-blue-600"
        >
          {showPicker ? "Hide Calendar" : "Select Date Range"}
        </button>

        <button
          onClick={fetchResources}
          className="px-4 py-2 bg-green-500 text-white rounded hover:bg-green-600"
        >
          Refresh
        </button>

        <span className="text-gray-600 ml-2 text-sm">
          Range: {format(range[0].startDate, "MMM dd")} –{" "}
          {format(range[0].endDate, "MMM dd")}
        </span>

        {/* Service filter (optional) */}
        <div className="ml-auto flex items-center gap-2">
          <label className="text-sm text-gray-700">Filter by service:</label>
          <select
            value={selectedService}
            onChange={(e) => setSelectedService(e.target.value)}
            className="px-3 py-2 border rounded bg-white shadow-sm text-sm"
          >
            <option value="">All</option>
            {uniqueServices.map((svc, i) => (
              <option key={i} value={svc}>
                {svc}
              </option>
            ))}
          </select>
        </div>
      </div>

      {/* Calendar */}
      {showPicker && (
        <div className="bg-white p-4 shadow rounded-lg w-fit mb-6">
          <DateRange
            editableDateInputs={true}
            onChange={(item) => setRange([item.selection])}
            moveRangeOnFirstSelection={false}
            ranges={range}
            maxDate={new Date()}
          />
        </div>
      )}

      {/* Info / message */}
      {apiMessage && (
        <div className="mb-4 text-sm text-amber-600 bg-amber-50 border border-amber-200 px-3 py-2 rounded">
          {apiMessage}
        </div>
      )}

      {/* Table */}
      {loading ? (
        <p className="text-gray-400">Loading resource-level data...</p>
      ) : data.length === 0 ? (
        <p className="text-gray-500">
          No resource-level rows returned for this range.
        </p>
      ) : (
        <div className="overflow-x-auto bg-white shadow rounded-lg">
          <table className="min-w-full divide-y divide-gray-200 text-sm">
            <thead className="bg-gray-100">
              <tr>
                <th className="px-4 py-2 text-left font-medium text-gray-500 uppercase">
                  Date
                </th>
                <th className="px-4 py-2 text-left font-medium text-gray-500 uppercase">
                  Service
                </th>
                <th className="px-4 py-2 text-left font-medium text-gray-500 uppercase">
                  Resource ID
                </th>
                <th className="px-4 py-2 text-left font-medium text-gray-500 uppercase">
                  Cost ($)
                </th>
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-100">
              {data.map((row, i) => (
                <tr key={i} className="hover:bg-gray-50">
                  <td className="px-4 py-2 text-gray-700">{row.day}</td>
                  <td className="px-4 py-2 text-gray-700">{row.service}</td>
                  <td className="px-4 py-2 text-gray-700">
                    {row.resource_id || "-"}
                  </td>
                  <td className="px-4 py-2 text-gray-700">
                    {Number(row.cost || 0).toFixed(6)}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}
