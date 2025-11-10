import axios from "axios";
const api = import.meta.env.VITE_API_URL;

export const getCosts = async (start, end) => {
  const res = await axios.get(`${api}/api/costs`, { params: { start, end } });
  return res.data.data;
};
