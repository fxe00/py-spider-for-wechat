<template>
  <Layout>
    <el-card>
      <div class="card-title">爬取日志</div>
      <div class="search-bar">
        <el-input
          v-model.number="logLimit"
          size="small"
          type="number"
          style="width: 160px"
          placeholder="拉取条数（默认200）"
        />
        <el-button size="small" type="primary" plain style="margin-left: 8px" @click="fetchLogs" :loading="loading.logs">
          刷新
        </el-button>
      </div>
      <el-table :data="logsPaged" style="width: 100%; margin-top: 10px" size="small" stripe border>
        <el-table-column fixed type="index" label="序号" width="60" />
        <el-table-column prop="target_name" label="公众号" />
        <el-table-column prop="status" label="状态" width="90" />
        <el-table-column prop="message" label="消息" />
        <el-table-column label="时间" width="180">
          <template #default="scope">{{ formatTime(scope.row.created_at) }}</template>
        </el-table-column>
      </el-table>
      <div class="pager spaced">
        <el-pagination
          background
          small
          layout="total, sizes, prev, pager, next, jumper"
          :page-sizes="[10, 20, 50, 100]"
          :page-size="logsPageSize"
          :total="logs.length"
          :current-page="logsPage"
          @size-change="handleLogSizeChange"
          @current-change="handleLogCurrentChange"
        />
      </div>
    </el-card>
  </Layout>
</template>

<script setup>
import { ref, computed, onMounted } from "vue";
import dayjs from "dayjs";
import http from "../api/http";
import { ElMessage } from "element-plus";
import Layout from "./Layout.vue";

const logs = ref([]);
const loading = ref({ logs: false });
const logLimit = ref(200);
const logsPage = ref(1);
const logsPageSize = ref(10);

const formatTime = (val) => (val ? dayjs(val).format("YYYY-MM-DD HH:mm") : "");

const fetchLogs = async () => {
  loading.value.logs = true;
  try {
    const { data } = await http.get("/logs", { params: { limit: logLimit.value } });
    logs.value = data;
  } catch {
    ElMessage.error("获取日志失败");
  } finally {
    loading.value.logs = false;
  }
};

const logsPaged = computed(() => {
  const start = (logsPage.value - 1) * logsPageSize.value;
  return logs.value.slice(start, start + logsPageSize.value);
});

const handleLogSizeChange = (val) => {
  logsPageSize.value = val;
  logsPage.value = 1;
};

const handleLogCurrentChange = (val) => {
  logsPage.value = val;
};

onMounted(() => {
  fetchLogs();
});
</script>

<style scoped>
.card-title {
  font-weight: bold;
  margin-bottom: 8px;
  display: flex;
  align-items: center;
  gap: 8px;
}
.search-bar {
  display: flex;
  align-items: center;
  gap: 8px;
}
.pager {
  display: flex;
  justify-content: flex-end;
}
.pager.spaced {
  margin-top: 16px;
}
</style>

