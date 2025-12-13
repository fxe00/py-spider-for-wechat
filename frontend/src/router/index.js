import { createRouter, createWebHistory } from "vue-router";
import Login from "../views/Login.vue";
import Config from "../views/Config.vue";
import Articles from "../views/Articles.vue";
import Logs from "../views/Logs.vue";
import { useAuthStore } from "../stores/auth";

const router = createRouter({
  history: createWebHistory(),
  routes: [
    { path: "/login", component: Login },
    { path: "/config", component: Config },
    { path: "/articles", component: Articles },
    { path: "/logs", component: Logs },
    { path: "/", redirect: "/articles" },
  ],
});

router.beforeEach((to, _from, next) => {
  const auth = useAuthStore();
  if (to.path !== "/login" && !auth.token) {
    next("/login");
  } else {
    next();
  }
});

export default router;

