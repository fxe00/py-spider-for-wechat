<template>
  <div class="layout">
    <el-container>
      <el-header class="header">
        <div class="brand">
          <svg width="28" height="28" viewBox="0 0 1024 1024" fill="none">
            <path d="M170 240c0-26.5 21.5-48 48-48h588c26.5 0 48 21.5 48 48v544c0 26.5-21.5 48-48 48H218c-26.5 0-48-21.5-48-48V240z" fill="#409EFF" opacity=".15"/>
            <path d="M256 320a32 32 0 0 1 32-32h448a32 32 0 1 1 0 64H288a32 32 0 0 1-32-32zM320 480a32 32 0 0 1 32-32h384a32 32 0 1 1 0 64H352a32 32 0 0 1-32-32zM320 640a32 32 0 0 1 32-32h256a32 32 0 1 1 0 64H352a32 32 0 0 1-32-32z" fill="#409EFF"/>
          </svg>
          <span class="brand-title">公众号爬取订阅平台</span>
        </div>
        <div class="header-actions">
          <el-button round size="small" @click="logout">退出</el-button>
        </div>
      </el-header>
      <el-container class="page-container">
        <el-aside width="220px" class="aside">
          <a-menu mode="inline" v-model:selectedKeys="menuKeys" @select="onSelect">
            <a-menu-item key="config">
              <template #icon><SettingOutlined /></template>
              配置
            </a-menu-item>
            <a-menu-item key="articles">
              <template #icon><FileTextOutlined /></template>
              文章列表
            </a-menu-item>
            <a-menu-item key="logs">
              <template #icon><ProfileOutlined /></template>
              爬取日志
            </a-menu-item>
          </a-menu>
        </el-aside>
        <el-main class="main-shell">
          <el-card shadow="hover" class="card-shell">
            <slot />
          </el-card>
        </el-main>
      </el-container>
    </el-container>
  </div>
</template>

<script setup>
import { ref, watch } from "vue";
import { useRouter, useRoute } from "vue-router";
import { SettingOutlined, FileTextOutlined, ProfileOutlined } from "@ant-design/icons-vue";
import { useAuthStore } from "../stores/auth";

const router = useRouter();
const route = useRoute();
const auth = useAuthStore();

// 根据当前路由设置菜单选中项
const getMenuKey = () => {
  if (route.path === "/config") return "config";
  if (route.path === "/articles") return "articles";
  if (route.path === "/logs") return "logs";
  return "articles"; // 默认
};

const menuKeys = ref([getMenuKey()]);

// 监听路由变化，更新菜单选中项
watch(() => route.path, () => {
  menuKeys.value = [getMenuKey()];
}, { immediate: true });

const onSelect = ({ key }) => {
  menuKeys.value = [key];
  if (key === "config") router.push("/config");
  else if (key === "articles") router.push("/articles");
  else if (key === "logs") router.push("/logs");
};

const logout = () => {
  auth.logout();
  router.push("/login");
};
</script>

<style scoped>
.layout {
  background: #eef2f7;
  min-height: 100vh;
}
.header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  background: #fff;
  box-shadow: 0 6px 20px rgba(0, 0, 0, 0.06);
  padding: 12px 24px;
}
.page-container {
  width: 100%;
  margin: 0;
  padding: 0 16px 16px;
}
.card-shell {
  border-radius: 8px;
  min-height: calc(100vh - 120px);
}
.main-shell {
  padding: 16px;
}
.brand {
  display: flex;
  align-items: center;
  gap: 12px;
}
.brand-title {
  font-size: 18px;
  font-weight: 600;
  color: #303133;
}
.aside {
  background: #fff;
  border-radius: 8px;
  margin-right: 16px;
  padding: 16px 0;
}
</style>

