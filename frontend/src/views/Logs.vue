<template>
  <Layout>
    <div class="logs-page">
      <!-- 统计卡片 -->
      <div class="stats-cards">
        <el-card class="stat-card" shadow="hover">
          <div class="stat-content">
            <div class="stat-icon total">
              <el-icon><Document /></el-icon>
            </div>
            <div class="stat-info">
              <div class="stat-value">{{ logs.length }}</div>
              <div class="stat-label">总日志数</div>
            </div>
          </div>
        </el-card>
        <el-card class="stat-card" shadow="hover">
          <div class="stat-content">
            <div class="stat-icon success">
              <el-icon><CircleCheck /></el-icon>
            </div>
            <div class="stat-info">
              <div class="stat-value">{{ successCount }}</div>
              <div class="stat-label">成功次数</div>
            </div>
          </div>
        </el-card>
        <el-card class="stat-card" shadow="hover">
          <div class="stat-content">
            <div class="stat-icon error">
              <el-icon><CircleClose /></el-icon>
            </div>
            <div class="stat-info">
              <div class="stat-value">{{ errorCount }}</div>
              <div class="stat-label">失败次数</div>
            </div>
          </div>
        </el-card>
        <el-card class="stat-card" shadow="hover">
          <div class="stat-content">
            <div class="stat-icon running">
              <el-icon><Loading /></el-icon>
            </div>
            <div class="stat-info">
              <div class="stat-value">{{ runningCount }}</div>
              <div class="stat-label">进行中</div>
            </div>
          </div>
        </el-card>
      </div>

      <!-- 筛选栏 -->
      <el-card class="filter-card" shadow="hover">
        <div class="filter-header">
          <div class="filter-title">
            <el-icon><Filter /></el-icon>
            <span>筛选条件</span>
          </div>
          <div class="filter-actions">
            <el-input
              v-model="targetNameFilter"
              size="default"
              placeholder="搜索公众号名称..."
              clearable
              style="width: 200px"
              @clear="fetchLogs"
            >
              <template #prefix>
                <el-icon><Search /></el-icon>
              </template>
            </el-input>
            <el-select
              v-model="statusFilter"
              size="default"
              placeholder="状态筛选"
              clearable
              style="width: 140px"
              @change="fetchLogs"
            >
              <el-option label="全部" value="" />
              <el-option label="开始" value="start" />
              <el-option label="进行中" value="progress" />
              <el-option label="完成" value="finish" />
              <el-option label="错误" value="error" />
            </el-select>
            <el-input-number
              v-model="logLimit"
              size="default"
              :min="50"
              :max="1000"
              :step="50"
              style="width: 140px"
            />
            <el-button size="default" type="primary" :icon="Refresh" @click="fetchLogs" :loading="loading.logs">
              刷新
            </el-button>
          </div>
        </div>
      </el-card>

      <!-- 日志列表 -->
      <el-card class="logs-card" shadow="hover">
        <el-table
          :data="filteredLogsPaged"
          style="width: 100%"
          size="default"
          stripe
          border
          :row-class-name="getRowClassName"
        >
          <el-table-column fixed type="index" label="序号" width="70" />
          <el-table-column prop="target_name" label="公众号" width="180">
            <template #default="scope">
              <el-tag size="small" type="info">{{ scope.row.target_name || "未知" }}</el-tag>
            </template>
          </el-table-column>
          <el-table-column prop="status" label="状态" width="100">
            <template #default="scope">
              <el-tag :type="getStatusType(scope.row.status)" size="small">
                {{ getStatusLabel(scope.row.status) }}
              </el-tag>
            </template>
          </el-table-column>
          <el-table-column prop="step" label="步骤" width="140">
            <template #default="scope">
              <span v-if="scope.row.step" class="step-text">{{ getStepLabel(scope.row.step) }}</span>
              <span v-else class="text-muted">-</span>
            </template>
          </el-table-column>
          <el-table-column prop="message" label="消息" min-width="300" show-overflow-tooltip />
          <el-table-column label="详细信息" width="120">
            <template #default="scope">
              <el-button
                size="small"
                type="primary"
                link
                :icon="View"
                @click="showLogDetail(scope.row)"
              >
                查看详情
              </el-button>
            </template>
          </el-table-column>
          <el-table-column label="时间" width="180" fixed="right">
            <template #default="scope">{{ formatTime(scope.row.created_at) }}</template>
          </el-table-column>
        </el-table>
        <div class="pager-wrapper">
          <el-pagination
            background
            layout="total, sizes, prev, pager, next, jumper"
            :page-sizes="[10, 20, 50, 100]"
            :page-size="logsPageSize"
            :total="filteredLogs.length"
            :current-page="logsPage"
            @size-change="handleLogSizeChange"
            @current-change="handleLogCurrentChange"
          />
        </div>
      </el-card>

      <!-- 日志详情对话框 -->
      <el-dialog v-model="logDetailDialog.visible" title="爬取日志详情" width="800px">
        <el-skeleton :rows="6" animated :loading="logDetailDialog.loading" />
        <div v-if="!logDetailDialog.loading && logDetailDialog.data" class="log-detail-content">
          <!-- 基本信息 -->
          <div class="detail-section">
            <h3 class="section-title">
              <el-icon><InfoFilled /></el-icon>
              <span>基本信息</span>
            </h3>
            <el-descriptions :column="2" border size="small">
              <el-descriptions-item label="公众号">
                <el-tag size="small" type="info">{{ logDetailDialog.data.target_name || "未知" }}</el-tag>
              </el-descriptions-item>
              <el-descriptions-item label="状态">
                <el-tag :type="getStatusType(logDetailDialog.data.status)" size="small">
                  {{ getStatusLabel(logDetailDialog.data.status) }}
                </el-tag>
              </el-descriptions-item>
              <el-descriptions-item label="步骤">
                {{ getStepLabel(logDetailDialog.data.step) || "-" }}
              </el-descriptions-item>
              <el-descriptions-item label="时间">
                {{ formatTime(logDetailDialog.data.created_at) }}
              </el-descriptions-item>
              <el-descriptions-item label="消息" :span="2">
                {{ logDetailDialog.data.message }}
              </el-descriptions-item>
            </el-descriptions>
          </div>

          <!-- 爬取流程 -->
          <div class="detail-section">
            <h3 class="section-title">
              <el-icon><Operation /></el-icon>
              <span>爬取流程</span>
            </h3>
            <div class="flow-chart">
              <div
                v-for="(step, index) in flowSteps"
                :key="index"
                class="flow-step"
                :class="{ active: isStepActive(step.key, logDetailDialog.data) }"
              >
                <div class="step-icon">
                  <el-icon v-if="isStepActive(step.key, logDetailDialog.data)">
                    <CircleCheck />
                  </el-icon>
                  <el-icon v-else-if="isStepError(step.key, logDetailDialog.data)">
                    <CircleClose />
                  </el-icon>
                  <el-icon v-else>
                    <Clock />
                  </el-icon>
                </div>
                <div class="step-content">
                  <div class="step-title">{{ step.title }}</div>
                  <div class="step-desc">{{ step.desc }}</div>
                </div>
                <div v-if="index < flowSteps.length - 1" class="step-arrow">
                  <el-icon><ArrowRight /></el-icon>
                </div>
              </div>
            </div>
          </div>

          <!-- 详细信息 -->
          <div v-if="hasDetails(logDetailDialog.data)" class="detail-section">
            <h3 class="section-title">
              <el-icon><Document /></el-icon>
              <span>详细信息</span>
            </h3>
            <el-descriptions :column="2" border size="small">
              <el-descriptions-item v-if="logDetailDialog.data.articles_count !== undefined" label="文章总数">
                {{ logDetailDialog.data.articles_count }} 篇
              </el-descriptions-item>
              <el-descriptions-item v-if="logDetailDialog.data.new_count !== undefined" label="新入库">
                {{ logDetailDialog.data.new_count }} 篇
              </el-descriptions-item>
              <el-descriptions-item v-if="logDetailDialog.data.fakeid" label="FakeID">
                <el-text copyable>{{ logDetailDialog.data.fakeid }}</el-text>
              </el-descriptions-item>
              <el-descriptions-item v-if="logDetailDialog.data.avatar_fetched !== undefined" label="头像获取">
                <el-tag :type="logDetailDialog.data.avatar_fetched ? 'success' : 'warning'" size="small">
                  {{ logDetailDialog.data.avatar_fetched ? "成功" : "失败" }}
                </el-tag>
              </el-descriptions-item>
              <el-descriptions-item v-else label="头像状态">
                <el-tag type="info" size="small">未记录</el-tag>
                <span class="text-muted" style="margin-left: 8px; font-size: 12px;">（可能已在之前获取）</span>
              </el-descriptions-item>
              <el-descriptions-item v-if="logDetailDialog.data.avatar_size" label="头像大小">
                {{ formatSize(logDetailDialog.data.avatar_size) }}
              </el-descriptions-item>
              <el-descriptions-item v-if="logDetailDialog.data.duration_ms" label="耗时">
                {{ formatDuration(logDetailDialog.data.duration_ms) }}
              </el-descriptions-item>
              <el-descriptions-item v-if="logDetailDialog.data.page_num" label="爬取页数">
                {{ logDetailDialog.data.page_num }} 页
              </el-descriptions-item>
              <el-descriptions-item v-if="logDetailDialog.data.error_type" label="错误类型">
                <el-tag type="danger" size="small">{{ logDetailDialog.data.error_type }}</el-tag>
              </el-descriptions-item>
            </el-descriptions>
          </div>
        </div>
        <template #footer>
          <el-button type="primary" @click="logDetailDialog.visible = false">关闭</el-button>
        </template>
      </el-dialog>
    </div>
  </Layout>
</template>

<script setup>
import { ref, reactive, computed, onMounted } from "vue";
import dayjs from "dayjs";
import http from "../api/http";
import { ElMessage } from "element-plus";
import {
  Document,
  CircleCheck,
  CircleClose,
  Loading,
  Filter,
  Refresh,
  Search,
  View,
  InfoFilled,
  Operation,
  Clock,
  ArrowRight,
} from "@element-plus/icons-vue";
import Layout from "./Layout.vue";

const logs = ref([]);
const loading = ref({ logs: false });
const logLimit = ref(200);
const logsPage = ref(1);
const logsPageSize = ref(20);
const targetNameFilter = ref("");
const statusFilter = ref("");

const formatTime = (val) => (val ? dayjs(val).format("YYYY-MM-DD HH:mm:ss") : "");

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

// 统计计算
const successCount = computed(() => {
  return logs.value.filter((log) => log.status === "finish").length;
});

const errorCount = computed(() => {
  return logs.value.filter((log) => log.status === "error").length;
});

const runningCount = computed(() => {
  return logs.value.filter((log) => log.status === "start" || log.status === "progress").length;
});

// 筛选日志
const filteredLogs = computed(() => {
  let result = logs.value;
  if (targetNameFilter.value) {
    result = result.filter((log) =>
      log.target_name?.toLowerCase().includes(targetNameFilter.value.toLowerCase())
    );
  }
  if (statusFilter.value) {
    result = result.filter((log) => log.status === statusFilter.value);
  }
  return result;
});

const filteredLogsPaged = computed(() => {
  const start = (logsPage.value - 1) * logsPageSize.value;
  return filteredLogs.value.slice(start, start + logsPageSize.value);
});

// 状态相关
const getStatusType = (status) => {
  const map = {
    start: "info",
    progress: "warning",
    finish: "success",
    error: "danger",
  };
  return map[status] || "info";
};

const getStatusLabel = (status) => {
  const map = {
    start: "开始",
    progress: "进行中",
    finish: "完成",
    error: "错误",
  };
  return map[status] || status;
};

const getStepLabel = (step) => {
  const map = {
    初始化: "初始化",
    获取fakeid: "获取FakeID",
    重新获取fakeid: "重新获取FakeID",
    获取头像: "获取头像",
    下载头像: "下载头像",
    保存头像: "保存头像",
    拉取文章: "拉取文章",
    重试拉取文章: "重试拉取文章",
    保存文章: "保存文章",
    完成: "完成",
  };
  return map[step] || step;
};

const getRowClassName = ({ row }) => {
  if (row.status === "error") return "error-row";
  if (row.status === "finish") return "success-row";
  return "";
};

// 日志详情
const logDetailDialog = reactive({
  visible: false,
  loading: false,
  data: null,
});

const showLogDetail = (row) => {
  logDetailDialog.visible = true;
  logDetailDialog.loading = false;
  logDetailDialog.data = row;
};

// 流程步骤
const flowSteps = [
  { key: "init", title: "初始化", desc: "开始爬取任务" },
  { key: "fakeid", title: "获取FakeID", desc: "查询或使用缓存的FakeID" },
  { key: "avatar", title: "获取头像", desc: "下载并保存公众号头像" },
  { key: "articles", title: "拉取文章", desc: "获取文章列表" },
  { key: "save", title: "保存数据", desc: "去重并保存到数据库" },
  { key: "finish", title: "完成", desc: "爬取任务完成" },
];

const isStepActive = (stepKey, logData) => {
  const step = logData?.step || "";
  const status = logData?.status || "";
  
  if (stepKey === "init") return status === "start" || status === "progress" || status === "finish";
  if (stepKey === "fakeid") return step.includes("fakeid") || status === "finish";
  if (stepKey === "avatar") return step.includes("头像") || status === "finish";
  if (stepKey === "articles") return step.includes("文章") || status === "finish";
  if (stepKey === "save") return step.includes("保存") || status === "finish";
  if (stepKey === "finish") return status === "finish";
  return false;
};

const isStepError = (stepKey, logData) => {
  return logData?.status === "error" && isStepActive(stepKey, logData);
};

const hasDetails = (logData) => {
  return (
    logData?.articles_count !== undefined ||
    logData?.new_count !== undefined ||
    logData?.fakeid ||
    logData?.avatar_fetched !== undefined ||
    logData?.duration_ms ||
    logData?.error_type
  );
};

const formatSize = (bytes) => {
  if (!bytes) return "-";
  if (bytes < 1024) return `${bytes} B`;
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
  return `${(bytes / (1024 * 1024)).toFixed(1)} MB`;
};

const formatDuration = (ms) => {
  if (!ms) return "-";
  if (ms < 1000) return `${ms} 毫秒`;
  if (ms < 60000) return `${(ms / 1000).toFixed(1)} 秒`;
  return `${(ms / 60000).toFixed(1)} 分钟`;
};

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
.logs-page {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

/* 统计卡片 */
.stats-cards {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 16px;
  margin-bottom: 8px;
}

.stat-card {
  transition: transform 0.2s, box-shadow 0.2s;
}

.stat-card:hover {
  transform: translateY(-2px);
}

.stat-content {
  display: flex;
  align-items: center;
  gap: 16px;
}

.stat-icon {
  width: 56px;
  height: 56px;
  border-radius: 12px;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 24px;
}

.stat-icon.total {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: white;
}

.stat-icon.success {
  background: linear-gradient(135deg, #43e97b 0%, #38f9d7 100%);
  color: white;
}

.stat-icon.error {
  background: linear-gradient(135deg, #fa709a 0%, #fee140 100%);
  color: white;
}

.stat-icon.running {
  background: linear-gradient(135deg, #4facfe 0%, #00f2fe 100%);
  color: white;
}

.stat-info {
  flex: 1;
}

.stat-value {
  font-size: 28px;
  font-weight: bold;
  color: #303133;
  line-height: 1;
  margin-bottom: 8px;
}

.stat-label {
  font-size: 14px;
  color: #909399;
}

/* 筛选卡片 */
.filter-card {
  border-radius: 8px;
}

.filter-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.filter-title {
  font-size: 16px;
  font-weight: 600;
  color: #303133;
  display: flex;
  align-items: center;
  gap: 8px;
}

.filter-actions {
  display: flex;
  gap: 12px;
  align-items: center;
}

/* 日志卡片 */
.logs-card {
  border-radius: 8px;
}

.pager-wrapper {
  margin-top: 16px;
  display: flex;
  justify-content: flex-end;
}

.step-text {
  font-size: 13px;
  color: #606266;
}

.text-muted {
  color: #909399;
  font-size: 13px;
}

/* 表格行样式 */
:deep(.error-row) {
  background-color: #fef0f0;
}

:deep(.success-row) {
  background-color: #f0f9ff;
}

/* 日志详情 */
.log-detail-content {
  padding: 0 8px;
}

.detail-section {
  margin-bottom: 24px;
}

.section-title {
  font-size: 16px;
  font-weight: 600;
  color: #303133;
  margin-bottom: 12px;
  display: flex;
  align-items: center;
  gap: 8px;
}

/* 流程图 */
.flow-chart {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 20px;
  background: #f5f7fa;
  border-radius: 8px;
  overflow-x: auto;
}

.flow-step {
  display: flex;
  align-items: center;
  gap: 8px;
  flex-shrink: 0;
  opacity: 0.5;
  transition: opacity 0.3s;
}

.flow-step.active {
  opacity: 1;
}

.step-icon {
  width: 40px;
  height: 40px;
  border-radius: 50%;
  background: #e4e7ed;
  display: flex;
  align-items: center;
  justify-content: center;
  color: #909399;
  font-size: 18px;
}

.flow-step.active .step-icon {
  background: #409eff;
  color: white;
}

.flow-step.error .step-icon {
  background: #f56c6c;
  color: white;
}

.step-content {
  min-width: 120px;
}

.step-title {
  font-weight: 600;
  color: #303133;
  margin-bottom: 4px;
}

.step-desc {
  font-size: 12px;
  color: #909399;
}

.step-arrow {
  color: #c0c4cc;
  font-size: 20px;
  margin: 0 4px;
}

.flow-step.active .step-arrow {
  color: #409eff;
}
</style>
