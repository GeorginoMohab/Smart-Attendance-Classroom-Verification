import axios from "axios";

const api = axios.create({
  baseURL: "http://192.168.43.138:3000",
  
});

export default api;