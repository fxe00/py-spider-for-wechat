<template>
  <div class="login-wrapper">
    <div class="login-hero">
      <div class="brand">
        <svg width="46" height="46" viewBox="0 0 1024 1024" fill="none">
          <path d="M170 240c0-26.5 21.5-48 48-48h588c26.5 0 48 21.5 48 48v544c0 26.5-21.5 48-48 48H218c-26.5 0-48-21.5-48-48V240z" fill="#409EFF" opacity=".15"/>
          <path d="M256 320a32 32 0 0 1 32-32h448a32 32 0 1 1 0 64H288a32 32 0 0 1-32-32zM320 480a32 32 0 0 1 32-32h384a32 32 0 1 1 0 64H352a32 32 0 0 1-32-32zM320 640a32 32 0 0 1 32-32h256a32 32 0 1 1 0 64H352a32 32 0 0 1-32-32z" fill="#409EFF"/>
        </svg>
        <div>
          <div class="brand-title">公众号爬取订阅平台</div>
          <div class="brand-sub">安全、自动、可视化的采集管理</div>
        </div>
      </div>
    </div>
    <div class="login-panel">
      <div class="panel-card">
        <div class="panel-title">登录</div>
        <el-form @submit.prevent="onSubmit" :model="form" label-position="top">
          <el-form-item label="用户名">
            <el-input v-model="form.username" size="large" />
          </el-form-item>
          <el-form-item label="密码">
            <el-input v-model="form.password" type="password" show-password size="large" />
          </el-form-item>
          <el-button type="primary" size="large" style="width: 100%" @click="onSubmit" :loading="loading">
            立即登录
          </el-button>
        </el-form>
        <p class="hint">默认管理员：admin / admin123（请部署时修改）</p>
      </div>
    </div>
  </div>
</template>

<script setup>
import { reactive, ref } from "vue";
import http from "../api/http";
import { useAuthStore } from "../stores/auth";
import { ElMessage } from "element-plus";
import { useRouter } from "vue-router";

const router = useRouter();
const auth = useAuthStore();
const form = reactive({ username: "", password: "" });
const loading = ref(false);

const onSubmit = async () => {
  loading.value = true;
  try {
    const { data } = await http.post("/auth/login", form);
    auth.setToken(data.token, data.username);
    ElMessage.success("登录成功");
    router.push("/articles");
  } catch (e) {
    ElMessage.error(e?.response?.data?.message || "登录失败");
  } finally {
    loading.value = false;
  }
};
</script>

<style scoped>
.login-wrapper {
  min-height: 100vh;
  display: grid;
  grid-template-columns: 1.2fr 1fr;
  background: linear-gradient(135deg, #edf2ff 0%, #f8fbff 50%, #f1f5f9 100%);
}
.login-hero {
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 80px;
}
.brand {
  display: flex;
  align-items: center;
  gap: 16px;
}
.brand-title {
  font-size: 28px;
  font-weight: 700;
  color: #1f2d3d;
}
.brand-sub {
  font-size: 14px;
  color: #6b7280;
  margin-top: 4px;
}
.login-panel {
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 60px;
}
.panel-card {
  width: 420px;
  background: #fff;
  border-radius: 16px;
  padding: 32px;
  box-shadow: 0 10px 30px rgba(0, 0, 0, 0.06);
}
.panel-title {
  font-size: 22px;
  font-weight: 700;
  margin-bottom: 16px;
  color: #1f2d3d;
}
.hint {
  margin-top: 12px;
  color: #9ca3af;
  font-size: 12px;
}
@media (max-width: 1024px) {
  .login-wrapper {
    grid-template-columns: 1fr;
    padding: 24px;
  }
  .login-hero {
    display: none;
  }
}
</style>

