import axios from "axios";
import { useAuthStore } from "../stores/auth";

const instance = axios.create({
  baseURL: "/api",
  timeout: 15000,
});

instance.interceptors.request.use((config) => {
  const auth = useAuthStore();
  if (auth.token) {
    config.headers.Authorization = `Bearer ${auth.token}`;
  }
  return config;
});

instance.interceptors.response.use(
  (resp) => resp,
  (error) => {
    if (error.response && error.response.status === 401) {
      const auth = useAuthStore();
      auth.clear();
      window.location.href = "/login";
    }
    return Promise.reject(error);
  }
);

export default instance;

