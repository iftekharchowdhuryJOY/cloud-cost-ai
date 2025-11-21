import axios from "axios";
const api = import.meta.env.VITE_API_URL;

export const explainService = async (service, days = 30, detail = false) => {
  const res = await axios.get(`${api}/api/ai/explain/${encodeURIComponent(service)}`, { params: { days, detail } });
  return res.data.data;
};

export const chatAi = async (messages, service = null, days = 30) => {
  const payload = { messages, service, days };
  const res = await axios.post(`${api}/api/ai/chat`, payload);
  return res.data.data;
};
