import { useEffect, useState } from "react";
import { DateRange } from "react-date-range";
import { getCosts } from "../api/costService";
import { format } from "date-fns";

import "react-date-range/dist/styles.css";
import "react-date-range/dist/theme/default.css";

import TotalSpendChart from "../components/TotalSpendChart";
import TopServicesChart from "../components/TopServicesChart";
import ServiceTrendChart from "../components/ServiceTrendChart";

export default function Dashboard() {
  const [data, setData] = useState([]);
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

  const fetchData = async () => {
    setLoading(true);

    const start = format(range[0].startDate, "yyyy-MM-dd");
    const end = format(range[0].endDate, "yyyy-MM-dd");

    const res = await getCosts(start, end);
    setData(res);

    setLoading(false);
  };

  useEffect(() => {
    fetchData();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  const uniqueServices = [...new Set(data.map((row) => row.service))];

  return (
    <div className="min-h-screen bg-gray-50 p-8">
      <h1 className="text-3xl font-bold text-gray-800 mb-6">
        💸 Cloud Cost AI – Spend Overview
      </h1>

      {/* --- Date controls --- */}
      <div className="flex items-center flex-wrap gap-4 mb-6">
        <button
          onClick={() => setShowPicker(!showPicker)}
          className="px-4 py-2 bg-blue-500 text-white rounded hover:bg-blue-600"
        >
          {showPicker ? "Hide Calendar" : "Select Date Range"}
        </button>

        <button
          onClick={fetchData}
          className="px-4 py-2 bg-green-500 text-white rounded hover:bg-green-600"
        >
          Refresh
        </button>

        <span className="text-gray-600 ml-2 text-sm">
          Showing: {format(range[0].startDate, "MMM dd")} –{" "}
          {format(range[0].endDate, "MMM dd")}
        </span>
      </div>

      {/* --- Calendar --- */}
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

      {/* --- Total Spend Chart --- */}
      {loading ? (
        <p className="text-gray-400 mb-4">Loading charts...</p>
      ) : (
        <TotalSpendChart data={data} />
      )}

      {/* --- Top 3 Services Chart --- */}
      {!loading && <TopServicesChart data={data} />}

      {/* --- Service Selector --- */}
      <div className="mt-8 mb-4">
        <label className="mr-3 font-medium text-gray-700">Service Trend:</label>

        <select
          value={selectedService}
          onChange={(e) => setSelectedService(e.target.value)}
          className="px-3 py-2 border rounded bg-white shadow-sm"
        >
          <option value="">-- Select a Service --</option>
          {uniqueServices.map((svc, i) => (
            <option key={i} value={svc}>
              {svc}
            </option>
          ))}
        </select>
      </div>

      {/* --- Selected Service Trend Chart --- */}
      {!loading && (
        <ServiceTrendChart
          data={data}
          selectedService={selectedService}
        />
      )}

      {/* --- Cost Table --- */}
      {loading ? (
        <p className="text-gray-400">Loading table...</p>
      ) : data.length === 0 ? (
        <p className="text-gray-500">No data found for selected range.</p>
      ) : (
        <div className="overflow-x-auto bg-white shadow rounded-lg mt-8">
          <table className="min-w-full divide-y divide-gray-200">
            <thead className="bg-gray-100">
              <tr>
                <th className="px-4 py-2 text-left text-xs font-medium text-gray-500 uppercase">
                  Date
                </th>
                <th className="px-4 py-2 text-left text-xs font-medium text-gray-500 uppercase">
                  Service
                </th>
                <th className="px-4 py-2 text-left text-xs font-medium text-gray-500 uppercase">
                  Cost ($)
                </th>
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-100">
              {data.map((row, i) => (
                <tr key={i} className="hover:bg-gray-50">
                  <td className="px-4 py-2 text-sm text-gray-700">{row.day}</td>
                  <td className="px-4 py-2 text-sm text-gray-700">{row.service}</td>
                  <td className="px-4 py-2 text-sm text-gray-700">
                    {Number(row.cost).toFixed(6)}
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
