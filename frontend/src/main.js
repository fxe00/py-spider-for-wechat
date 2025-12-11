import { createApp } from "vue";
import { createPinia } from "pinia";
import ElementPlus from "element-plus";
import Antd from "ant-design-vue";
import "element-plus/dist/index.css";
import "ant-design-vue/dist/reset.css";
import "./styles/global.css";
import App from "./App.vue";
import router from "./router";

const app = createApp(App);
app.use(createPinia());
app.use(router);
app.use(ElementPlus);
app.use(Antd);
app.mount("#app");

