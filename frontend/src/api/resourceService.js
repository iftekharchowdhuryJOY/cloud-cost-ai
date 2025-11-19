import axios from "axios";

const api = import.meta.env.VITE_API_URL;

export const getResourceCosts = async (start, end, service) => {
  const params = { start, end };
  if (service) params.service = service;

  try {
    const res = await axios.get(`${api}/api/costs/resources`, { params });
    // Our backend returns { data: [...], message?: string }
    return res.data;
  } catch (err) {
    console.error("Error fetching resource-level cost data:", err);
    return { data: [], message: "Error fetching data" };
  }
};
