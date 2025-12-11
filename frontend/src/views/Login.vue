<template>
  <div class="login-page">
    <el-card class="login-card">
      <h2>公众号爬取订阅平台</h2>
      <el-form @submit.prevent="onSubmit" :model="form" label-position="top">
        <el-form-item label="用户名">
          <el-input v-model="form.username" />
        </el-form-item>
        <el-form-item label="密码">
          <el-input v-model="form.password" type="password" show-password />
        </el-form-item>
        <el-button type="primary" style="width: 100%" @click="onSubmit" :loading="loading">
          登录
        </el-button>
      </el-form>
      <p class="hint">默认管理员：admin / admin123（请部署时修改）</p>
    </el-card>
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
    router.push("/");
  } catch (e) {
    ElMessage.error(e?.response?.data?.message || "登录失败");
  } finally {
    loading.value = false;
  }
};
</script>

<style scoped>
.login-page {
  min-height: 100vh;
  display: flex;
  align-items: center;
  justify-content: center;
  background: #f5f7fa;
}
.login-card {
  width: 360px;
}
.hint {
  margin-top: 12px;
  color: #999;
  font-size: 12px;
}
</style>

