import { defineStore } from "pinia";
import axios from "axios";

export const useAuthStore = defineStore("auth", {
  state: () => ({
    token: localStorage.getItem("token") || "",
    username: localStorage.getItem("username") || "",
  }),
  actions: {
    setToken(token, username) {
      this.token = token;
      this.username = username;
      localStorage.setItem("token", token);
      localStorage.setItem("username", username);
      axios.defaults.headers.common.Authorization = `Bearer ${token}`;
    },
    clear() {
      this.token = "";
      this.username = "";
      localStorage.removeItem("token");
      localStorage.removeItem("username");
      delete axios.defaults.headers.common.Authorization;
    },
  },
});

