import { useEffect, useState } from "react";
import { DateRange } from "react-date-range";
import { format } from "date-fns";
import axios from "axios";

export default function AnomalyDashboard() {
  const [data, setData] = useState([]);
  const [showPicker, setShowPicker] = useState(false);
  const [threshold, setThreshold] = useState(1.3);
  const [loading, setLoading] = useState(false);

  const [range, setRange] = useState([
    {
      startDate: new Date(new Date().setDate(new Date().getDate() - 14)),
      endDate: new Date(),
      key: "selection",
    },
  ]);

  const fetchAnomalies = async () => {
    setLoading(true);

    const startDate = new Date(range[0].startDate);
    const endDate = new Date(range[0].endDate);
    const days = Math.ceil((endDate - startDate) / (1000 * 60 * 60 * 24));
    const api = import.meta.env.VITE_API_URL;

    try {
      const res = await axios.get(`${api}/anomalies`, {
        params: { days, minImpact: threshold },
      });
      setData(res.data.results || []);
    } catch (e) {
      console.error("Anomaly fetch error:", e);
    }

    setLoading(false);
  };

  useEffect(() => {
    fetchAnomalies();
  }, []);

  return (
    <div className="min-h-screen bg-gray-50 p-8">
      <h1 className="text-3xl font-bold text-gray-800 mb-6">
        🚨 Anomaly Detection
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
          onClick={fetchAnomalies}
          className="px-4 py-2 bg-green-500 text-white rounded hover:bg-green-600"
        >
          Refresh
        </button>

        <span className="text-gray-600 ml-2 text-sm">
          Range: {format(range[0].startDate, "MMM dd")} –{" "}
          {format(range[0].endDate, "MMM dd")}
        </span>

        <div className="ml-auto flex items-center gap-2">
          <label className="text-sm">Threshold x</label>
          <input
            type="number"
            step="0.1"
            className="border px-2 py-1 rounded w-20"
            value={threshold}
            onChange={(e) => setThreshold(parseFloat(e.target.value))}
          />
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

      {/* Table */}
      {loading ? (
        <p className="text-gray-400">Loading anomalies...</p>
      ) : data.length === 0 ? (
        <p className="text-gray-500">No anomalies detected.</p>
      ) : (
        <div className="bg-white shadow rounded-lg overflow-x-auto">
          <table className="min-w-full divide-y divide-gray-200 text-sm">
            <thead className="bg-gray-100">
              <tr>
                <th className="px-4 py-2">Date</th>
                <th className="px-4 py-2">Impact (USD)</th>
                <th className="px-4 py-2">Type</th>
                <th className="px-4 py-2">Top Services</th>
                <th className="px-4 py-2">Score</th>
              </tr>
            </thead>
            <tbody>
              {data.map((row, i) => (
                <tr key={i} className="hover:bg-gray-50">
                  <td className="px-4 py-2">{row.day}</td>
                  <td className="px-4 py-2 font-bold text-red-600">${row.impact_usd.toFixed(2)}</td>
                  <td className="px-4 py-2">
                    <span className={`text-xs px-2 py-1 rounded ${
                      row.type === "trend_break"
                        ? "bg-red-100 text-red-700"
                        : "bg-yellow-100 text-yellow-700"
                    }`}>
                      {row.type === "trend_break" ? "Trend Break" : "Anomaly"}
                    </span>
                  </td>
                  <td className="px-4 py-2 text-sm">
                    {row.top_services?.map((s, j) => (
                      <div key={j}>{s.name}: +${s.delta_usd.toFixed(2)}</div>
                    ))}
                  </td>
                  <td className="px-4 py-2 text-xs text-gray-600">{row.score.toFixed(3)}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}
