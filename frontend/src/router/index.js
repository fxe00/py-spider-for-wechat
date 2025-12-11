import { createRouter, createWebHistory } from "vue-router";
import Login from "../views/Login.vue";
import Dashboard from "../views/Dashboard.vue";
import { useAuthStore } from "../stores/auth";

const router = createRouter({
  history: createWebHistory(),
  routes: [
    { path: "/login", component: Login },
    { path: "/", component: Dashboard },
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

