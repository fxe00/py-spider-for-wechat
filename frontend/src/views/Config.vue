<template>
  <Layout>
    <div class="config-page">
      <!-- 统计卡片 -->
      <div class="stats-cards">
        <el-card class="stat-card" shadow="hover">
          <div class="stat-content">
            <div class="stat-icon account">
              <el-icon><User /></el-icon>
            </div>
            <div class="stat-info">
              <div class="stat-value">{{ accounts.length }}</div>
              <div class="stat-label">登录账号</div>
            </div>
          </div>
        </el-card>
        <el-card class="stat-card" shadow="hover">
          <div class="stat-content">
            <div class="stat-icon target">
              <el-icon><Collection /></el-icon>
            </div>
            <div class="stat-info">
              <div class="stat-value">{{ targets.length }}</div>
              <div class="stat-label">公众号配置</div>
            </div>
          </div>
        </el-card>
        <el-card class="stat-card" shadow="hover">
          <div class="stat-content">
            <div class="stat-icon enabled">
              <el-icon><CircleCheck /></el-icon>
            </div>
            <div class="stat-info">
              <div class="stat-value">{{ enabledTargets }}</div>
              <div class="stat-label">已启用</div>
            </div>
          </div>
        </el-card>
        <el-card class="stat-card" shadow="hover">
          <div class="stat-content">
            <div class="stat-icon category">
              <el-icon><Folder /></el-icon>
            </div>
            <div class="stat-info">
              <div class="stat-value">{{ categoriesCount }}</div>
              <div class="stat-label">分类数量</div>
            </div>
          </div>
        </el-card>
      </div>

      <!-- 账号配置（上） -->
      <el-card class="config-card" shadow="hover">
        <div class="card-header">
          <div class="card-title">
            <el-icon><User /></el-icon>
            <span>账号配置</span>
          </div>
          <div class="card-actions">
            <el-button size="small" type="primary" :icon="Refresh" @click="fetchAccounts" :loading="loading.accounts">
              刷新
            </el-button>
            <el-button size="small" type="success" :icon="Plus" @click="openAccountDialog()">
              新增账号
            </el-button>
          </div>
        </div>
        <div class="search-bar">
          <el-input
            v-model="accountQuery"
            size="default"
            placeholder="搜索账号名称..."
            clearable
            style="width: 280px"
            @keydown.enter="fetchAccounts"
            @clear="fetchAccounts"
          >
            <template #prefix>
              <el-icon><Search /></el-icon>
            </template>
          </el-input>
        </div>
        <el-table :data="accountsPaged" style="width: 100%; margin-top: 10px" size="small" stripe border>
          <el-table-column fixed type="index" label="序号" width="60" />
          <el-table-column prop="name" label="名称" width="160" />
          <el-table-column label="更新时间" width="180">
            <template #default="scope">{{ formatTime(scope.row.updated_at) }}</template>
          </el-table-column>
          <el-table-column label="操作" width="200" fixed="right">
            <template #default="scope">
              <el-space size="small">
                <el-button size="small" link type="primary" @click="openAccountDialog(scope.row)">编辑</el-button>
                <el-button size="small" link type="danger" @click="removeAccount(scope.row)">删除</el-button>
              </el-space>
            </template>
          </el-table-column>
        </el-table>
        <div class="pager spaced">
          <el-pagination
            background
            small
            layout="total, sizes, prev, pager, next, jumper"
            :page-sizes="[5, 8, 10, 20]"
            :page-size="accountsPageSize"
            :total="accounts.length"
            :current-page="accountsPage"
            @size-change="handleAccountSizeChange"
            @current-change="handleAccountCurrentChange"
          />
        </div>
      </el-card>

      <!-- 公众号配置（下） -->
      <el-card class="config-card" shadow="hover">
        <div class="card-header">
          <div class="card-title">
            <el-icon><Collection /></el-icon>
            <span>公众号配置</span>
          </div>
          <div class="card-actions">
            <el-button size="small" type="primary" :icon="Refresh" @click="fetchTargets" :loading="loading.targets">
              刷新
            </el-button>
            <el-button size="small" type="success" :icon="Plus" @click="openTargetDialog()">
              新增公众号
            </el-button>
          </div>
        </div>
        <div class="search-bar">
          <el-input
            v-model="targetQuery"
            size="default"
            placeholder="搜索公众号名称..."
            clearable
            style="width: 280px"
            @keydown.enter="fetchTargets"
            @clear="fetchTargets"
          >
            <template #prefix>
              <el-icon><Search /></el-icon>
            </template>
          </el-input>
        </div>
        <el-table :data="targetsPaged" style="width: 100%; margin-top: 10px" size="small" stripe border>
          <el-table-column fixed type="index" label="序号" width="60" />
          <el-table-column prop="name" label="名称" width="180" />
          <el-table-column prop="category" label="分类" width="120" />
          <el-table-column label="调度" min-width="220">
            <template #default="scope">{{ renderSchedule(scope.row) }}</template>
          </el-table-column>
          <el-table-column label="上次运行" width="180">
            <template #default="scope">{{ formatTime(scope.row.last_run_at) }}</template>
          </el-table-column>
          <el-table-column prop="last_error" label="上次错误" min-width="240" />
            <el-table-column label="操作" width="380" fixed="right">
              <template #default="scope">
                <el-space size="small">
                  <el-button
                    type="primary"
                    size="small"
                    plain
                    class="square-btn"
                    :loading="triggerLoading[scope.row.id]"
                    @click="trigger(scope.row)"
                  >
                    立刻抓取
                  </el-button>
                  <el-button size="small" link type="info" @click="showTargetDetail(scope.row)">详情</el-button>
                  <el-button size="small" link type="primary" @click="openTargetDialog(scope.row)">编辑</el-button>
                  <el-button size="small" link type="danger" @click="removeTarget(scope.row)">删除</el-button>
                </el-space>
              </template>
            </el-table-column>
        </el-table>
        <div class="pager spaced">
          <el-pagination
            background
            small
            layout="total, sizes, prev, pager, next, jumper"
            :page-sizes="[20, 50, 100]"
            :page-size="targetsPageSize"
            :total="targets.length"
            :current-page="targetsPage"
            @size-change="handleTargetSizeChange"
            @current-change="handleTargetCurrentChange"
          />
        </div>
      </el-card>
    </div>

    <!-- 账号对话框（新增/编辑） -->
    <el-dialog v-model="accountDialog.visible" :title="accountDialog.isEdit ? '编辑账号' : '新增账号'" width="520px">
      <el-form :model="accountDialog.form" label-width="120px" label-position="left" class="dialog-form">
        <el-form-item label="名称">
          <el-input v-model="accountDialog.form.name" />
        </el-form-item>
        <el-form-item label="Token">
          <el-input v-model="accountDialog.form.token" />
        </el-form-item>
        <el-form-item label="Cookie">
          <el-input v-model="accountDialog.form.cookie" type="textarea" :rows="3" />
        </el-form-item>
        <el-form-item label="备注">
          <el-input v-model="accountDialog.form.remark" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="accountDialog.visible = false">取消</el-button>
        <el-button type="primary" :loading="accountDialog.loading" @click="submitAccount">保存</el-button>
      </template>
    </el-dialog>

    <!-- 公众号对话框（新增/编辑） -->
    <el-dialog v-model="targetDialog.visible" :title="targetDialog.isEdit ? '编辑公众号' : '新增公众号'" width="480px">
      <el-form :model="targetDialog.form" label-width="110px">
        <el-form-item label="公众号名称">
          <el-input v-model="targetDialog.form.name" />
        </el-form-item>
        <el-form-item label="分类">
          <el-select
            v-model="targetDialog.form.category"
            placeholder="选择或输入分类"
            filterable
            allow-create
            clearable
            style="width: 100%"
          >
            <el-option v-for="cat in categories" :key="cat" :label="cat" :value="cat" />
          </el-select>
        </el-form-item>
        <el-form-item label="绑定账号">
          <el-select v-model="targetDialog.form.account_id" placeholder="选择已有账号">
            <el-option v-for="a in accounts" :key="a.id" :label="a.name" :value="a.id" />
          </el-select>
        </el-form-item>
        <el-form-item label="调度类型">
          <el-radio-group v-model="targetDialog.form.schedule_mode">
            <el-radio-button label="daily">每日指定时刻</el-radio-button>
            <el-radio-button label="interval">固定间隔</el-radio-button>
            <el-radio-button label="cron">Cron 表达式</el-radio-button>
          </el-radio-group>
        </el-form-item>
        <template v-if="targetDialog.form.schedule_mode === 'interval'">
          <el-form-item label="间隔频率">
            <el-input-number v-model.number="targetDialog.form.freq_value" :min="1" style="width: 140px" />
            <el-select v-model="targetDialog.form.freq_unit" style="width: 120px; margin-left: 8px">
              <el-option label="分钟" value="minute" />
              <el-option label="小时" value="hour" />
              <el-option label="天" value="day" />
            </el-select>
          </el-form-item>
        </template>
        <template v-else-if="targetDialog.form.schedule_mode === 'daily'">
          <el-form-item label="每日时刻">
            <div class="daily-times">
              <el-time-select
                v-for="(t, idx) in targetDialog.form.daily_times"
                :key="idx"
                v-model="targetDialog.form.daily_times[idx]"
                style="width: 150px; margin-right: 8px"
                start="00:00"
                step="00:30"
                end="23:30"
              />
              <el-button size="small" @click="addDailyTime">添加时刻</el-button>
              <el-button
                size="small"
                type="danger"
                :disabled="targetDialog.form.daily_times.length <= 1"
                @click="removeDailyTime"
              >
                删除末尾
              </el-button>
            </div>
          </el-form-item>
        </template>
        <template v-else>
          <el-form-item label="Cron 表达式">
            <el-input v-model="targetDialog.form.cron_expr" placeholder="如：0 9,21 * * *" />
          </el-form-item>
        </template>
        <el-form-item label="biz(可选)">
          <el-input v-model="targetDialog.form.biz" />
        </el-form-item>
        <el-form-item label="启用">
          <el-switch v-model="targetDialog.form.enabled" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="targetDialog.visible = false">取消</el-button>
        <el-button type="primary" :loading="targetDialog.loading" @click="submitTarget">保存</el-button>
      </template>
    </el-dialog>

    <!-- 公众号详情对话框 -->
    <el-dialog v-model="targetDetailDialog.visible" title="公众号详情" width="600px">
      <div v-if="targetDetailDialog.loading" class="detail-loading">
        <el-icon class="is-loading"><Loading /></el-icon>
        <span>加载中...</span>
      </div>
      <div v-else-if="targetDetailDialog.data" class="target-detail">
        <div class="detail-header">
          <img
            v-if="targetDetailDialog.data.mp_avatar"
            :src="targetDetailDialog.data.mp_avatar"
            class="detail-avatar"
            @error="handleAvatarError"
          />
          <el-icon v-else class="detail-avatar-icon"><UserFilled /></el-icon>
          <div class="detail-title">
            <h3>{{ targetDetailDialog.data.name }}</h3>
            <p v-if="targetDetailDialog.data.mp_signature" class="detail-signature">
              {{ targetDetailDialog.data.mp_signature }}
            </p>
          </div>
        </div>
        <el-divider />
        <div class="detail-info">
          <el-descriptions :column="2" border>
            <el-descriptions-item label="分类">
              <el-tag v-if="targetDetailDialog.data.category" size="small" type="info">
                {{ targetDetailDialog.data.category }}
              </el-tag>
              <span v-else class="text-muted">-</span>
            </el-descriptions-item>
            <el-descriptions-item label="别名">
              {{ targetDetailDialog.data.mp_alias || "-" }}
            </el-descriptions-item>
            <el-descriptions-item label="服务类型">
              {{ targetDetailDialog.data.mp_service_type || "-" }}
            </el-descriptions-item>
            <el-descriptions-item label="认证类型">
              {{ targetDetailDialog.data.mp_verify_type || "-" }}
            </el-descriptions-item>
            <el-descriptions-item label="用户名">
              {{ targetDetailDialog.data.mp_user_name || "-" }}
            </el-descriptions-item>
            <el-descriptions-item label="biz">
              {{ targetDetailDialog.data.biz || "-" }}
            </el-descriptions-item>
            <el-descriptions-item label="调度模式">
              {{ renderSchedule(targetDetailDialog.data) }}
            </el-descriptions-item>
            <el-descriptions-item label="状态">
              <el-tag :type="targetDetailDialog.data.enabled ? 'success' : 'danger'" size="small">
                {{ targetDetailDialog.data.enabled ? "启用" : "禁用" }}
              </el-tag>
            </el-descriptions-item>
            <el-descriptions-item label="上次运行">
              {{ formatTime(targetDetailDialog.data.last_run_at) || "-" }}
            </el-descriptions-item>
            <el-descriptions-item label="创建时间">
              {{ formatTime(targetDetailDialog.data.created_at) || "-" }}
            </el-descriptions-item>
            <el-descriptions-item v-if="targetDetailDialog.data.last_error" label="上次错误" :span="2">
              <el-text type="danger">{{ targetDetailDialog.data.last_error }}</el-text>
            </el-descriptions-item>
          </el-descriptions>
        </div>
      </div>
      <template #footer>
        <el-button type="primary" @click="targetDetailDialog.visible = false">关闭</el-button>
      </template>
    </el-dialog>
  </Layout>
</template>

<script setup>
import { ref, reactive, onMounted, computed } from "vue";
import dayjs from "dayjs";
import http from "../api/http";
import { ElMessage, ElMessageBox } from "element-plus";
import { Loading, UserFilled, User, Collection, CircleCheck, Folder, Refresh, Plus, Search } from "@element-plus/icons-vue";
import Layout from "./Layout.vue";

const accounts = ref([]);
const targets = ref([]);
const categories = ref([]);
const loading = ref({ accounts: false, targets: false });
const triggerLoading = reactive({});
const accountQuery = ref("");
const targetQuery = ref("");
const accountsPage = ref(1);
const accountsPageSize = ref(8);
const targetsPage = ref(1);
const targetsPageSize = ref(20);

const accountDialog = reactive({
  visible: false,
  loading: false,
  isEdit: false,
  currentId: "",
  form: { name: "", token: "", cookie: "", remark: "" },
});

const targetDialog = reactive({
  visible: false,
  loading: false,
  isEdit: false,
  currentId: "",
  form: {
    name: "",
    category: "",
    account_id: "",
    schedule_mode: "daily",
    freq_value: 1,
    freq_unit: "hour",
    daily_times: ["09:00", "13:00", "18:00", "22:00"],
    cron_expr: "",
    biz: "",
    enabled: true,
  },
});

const targetDetailDialog = reactive({
  visible: false,
  loading: false,
  data: null,
});

const formatTime = (val) => (val ? dayjs(val).format("YYYY-MM-DD HH:mm") : "");

const fetchAccounts = async () => {
  loading.value.accounts = true;
  try {
    const { data } = await http.get("/mp-accounts", { params: { q: accountQuery.value } });
    accounts.value = data;
  } catch {
    ElMessage.error("获取账号失败");
  } finally {
    loading.value.accounts = false;
  }
};

const fetchTargets = async () => {
  loading.value.targets = true;
  try {
    const { data } = await http.get("/targets", { params: { q: targetQuery.value } });
    targets.value = data;
  } catch {
    ElMessage.error("获取公众号配置失败");
  } finally {
    loading.value.targets = false;
  }
};

const fetchCategories = async () => {
  try {
    const { data } = await http.get("/targets/categories");
    categories.value = data || [];
  } catch {
    // 忽略错误，分类是可选的
  }
};

const trigger = async (row) => {
  triggerLoading[row.id] = true;
  try {
    await http.post(`/targets/${row.id}/run`);
    ElMessage.success(`已下发任务：${row.name}`);
    fetchTargets();
  } catch (e) {
    ElMessage.error(e?.response?.data?.message || "下发失败");
  } finally {
    triggerLoading[row.id] = false;
  }
};

const openAccountDialog = (row) => {
  if (row) {
    accountDialog.isEdit = true;
    accountDialog.currentId = row.id;
    accountDialog.form = {
      name: row.name,
      token: row.token,
      cookie: row.cookie,
      remark: row.remark || "",
    };
  } else {
    accountDialog.isEdit = false;
    accountDialog.currentId = "";
    accountDialog.form = { name: "", token: "", cookie: "", remark: "" };
  }
  accountDialog.visible = true;
};

const submitAccount = async () => {
  const { name, token, cookie } = accountDialog.form;
  if (!name || !token || !cookie) {
    ElMessage.warning("请填写名称、token、cookie");
    return;
  }
  accountDialog.loading = true;
  try {
    if (accountDialog.isEdit) {
      await http.put(`/mp-accounts/${accountDialog.currentId}`, accountDialog.form);
    } else {
      await http.post("/mp-accounts", accountDialog.form);
    }
    ElMessage.success("保存成功");
    accountDialog.visible = false;
    fetchAccounts();
  } catch (e) {
    ElMessage.error(e?.response?.data?.message || "保存失败");
  } finally {
    accountDialog.loading = false;
  }
};

const removeAccount = (row) => {
  ElMessageBox.confirm("确定删除该账号吗？", "提示", { type: "warning" })
    .then(async () => {
      try {
        await http.delete(`/mp-accounts/${row.id}`);
        ElMessage.success("已删除");
        fetchAccounts();
      } catch (e) {
        ElMessage.error(e?.response?.data?.message || "删除失败");
      }
    })
    .catch(() => {});
};

const openTargetDialog = (row) => {
  fetchCategories(); // 刷新分类列表
  if (!accounts.value.length) {
    ElMessage.warning("请先添加登录账号");
    return;
  }
  if (row) {
    targetDialog.isEdit = true;
    targetDialog.currentId = row.id;
    const fv = toValueAndUnit(row.freq_minutes);
    targetDialog.form = {
      name: row.name,
      category: row.category || "",
      account_id: row.account_id,
      schedule_mode: row.schedule_mode || "daily",
      freq_value: fv.value,
      freq_unit: fv.unit,
      daily_times: row.daily_times && row.daily_times.length ? row.daily_times : ["09:00", "13:00", "18:00", "22:00"],
      cron_expr: row.cron_expr || "",
      biz: row.biz || "",
      enabled: row.enabled !== false,
    };
  } else {
    targetDialog.isEdit = false;
    targetDialog.currentId = "";
    targetDialog.form = {
      name: "",
      category: "",
      account_id: accounts.value[0].id || "",
      schedule_mode: "daily",
      freq_value: 1,
      freq_unit: "day",
      daily_times: ["09:00", "13:00", "18:00", "22:00"],
      cron_expr: "",
      biz: "",
      enabled: true,
    };
  }
  targetDialog.visible = true;
};

const submitTarget = async () => {
  const { name, account_id, freq_value, freq_unit, schedule_mode, daily_times, cron_expr } = targetDialog.form;
  if (!name || !account_id) {
    ElMessage.warning("请填写名称、绑定账号");
    return;
  }
  if (schedule_mode === "interval" && (!freq_value || !freq_unit)) {
    ElMessage.warning("请填写间隔频率");
    return;
  }
  if (schedule_mode === "daily" && (!daily_times || !daily_times.length)) {
    ElMessage.warning("请至少添加一个每日时间");
    return;
  }
  if (schedule_mode === "cron" && !cron_expr) {
    ElMessage.warning("请输入 cron 表达式");
    return;
  }
  const freq_minutes = convertToMinutes(freq_value, freq_unit);
  const payload = { ...targetDialog.form, freq_minutes };

  targetDialog.loading = true;
  try {
    if (targetDialog.isEdit) {
      await http.put(`/targets/${targetDialog.currentId}`, payload);
    } else {
      await http.post("/targets", payload);
    }
    ElMessage.success("保存成功");
    targetDialog.visible = false;
    fetchTargets();
  } catch (e) {
    ElMessage.error(e?.response?.data?.message || "保存失败");
  } finally {
    targetDialog.loading = false;
  }
};

const removeTarget = (row) => {
  ElMessageBox.confirm("确定删除该公众号配置吗？", "提示", { type: "warning" })
    .then(async () => {
      try {
        await http.delete(`/targets/${row.id}`);
        ElMessage.success("已删除");
        fetchTargets();
      } catch (e) {
        ElMessage.error(e?.response?.data?.message || "删除失败");
      }
    })
    .catch(() => {});
};

const showTargetDetail = async (row) => {
  targetDetailDialog.visible = true;
  targetDetailDialog.loading = true;
  targetDetailDialog.data = null;
  try {
    const { data } = await http.get(`/targets/${row.id}`);
    targetDetailDialog.data = data;
  } catch (e) {
    ElMessage.error(e?.response?.data?.message || "获取详情失败");
    targetDetailDialog.visible = false;
  } finally {
    targetDetailDialog.loading = false;
  }
};

const handleAvatarError = (event) => {
  event.target.style.display = "none";
};

const convertToMinutes = (value, unit) => {
  const v = Number(value) || 0;
  if (unit === "hour") return v * 60;
  if (unit === "day") return v * 1440;
  return v;
};

const toValueAndUnit = (minutes) => {
  const m = Number(minutes) || 0;
  if (m % 1440 === 0 && m !== 0) return { value: m / 1440, unit: "day" };
  if (m % 60 === 0 && m !== 0) return { value: m / 60, unit: "hour" };
  return { value: m || 60, unit: "minute" };
};

const renderSchedule = (row) => {
  const mode = row.schedule_mode || "interval";
  if (mode === "daily" && row.daily_times && row.daily_times.length) {
    return `每日 ${row.daily_times.join(", ")}`;
  }
  if (mode === "cron" && row.cron_expr) {
    return `cron: ${row.cron_expr}`;
  }
  const fv = toValueAndUnit(row.freq_minutes);
  const unitLabel = fv.unit === "day" ? "天" : fv.unit === "hour" ? "小时" : "分钟";
  return `每 ${fv.value}${unitLabel}`;
};

const addDailyTime = () => {
  targetDialog.form.daily_times.push("09:00");
};

const removeDailyTime = () => {
  if (targetDialog.form.daily_times.length > 1) {
    targetDialog.form.daily_times.pop();
  }
};

const accountsPaged = computed(() => {
  const start = (accountsPage.value - 1) * accountsPageSize.value;
  return accounts.value.slice(start, start + accountsPageSize.value);
});

const targetsPaged = computed(() => {
  const start = (targetsPage.value - 1) * targetsPageSize.value;
  return targets.value.slice(start, start + targetsPageSize.value);
});

const enabledTargets = computed(() => {
  return targets.value.filter(t => t.enabled !== false).length;
});

const categoriesCount = computed(() => {
  return availableCategories.value.length;
});

const handleAccountSizeChange = (val) => {
  accountsPageSize.value = val;
  accountsPage.value = 1;
};
const handleAccountCurrentChange = (val) => {
  accountsPage.value = val;
};
const handleTargetSizeChange = (val) => {
  targetsPageSize.value = val;
  targetsPage.value = 1;
};
const handleTargetCurrentChange = (val) => {
  targetsPage.value = val;
};

onMounted(() => {
  fetchAccounts();
  fetchTargets();
  fetchCategories();
});
</script>

<style scoped>
.config-page {
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

.stat-icon.account {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: white;
}

.stat-icon.target {
  background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%);
  color: white;
}

.stat-icon.enabled {
  background: linear-gradient(135deg, #4facfe 0%, #00f2fe 100%);
  color: white;
}

.stat-icon.category {
  background: linear-gradient(135deg, #43e97b 0%, #38f9d7 100%);
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

/* 配置卡片 */
.config-card {
  border-radius: 8px;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 16px;
  padding-bottom: 12px;
  border-bottom: 1px solid #ebeef5;
}

.card-title {
  font-size: 18px;
  font-weight: 600;
  color: #303133;
  display: flex;
  align-items: center;
  gap: 8px;
}

.card-actions {
  display: flex;
  gap: 8px;
}

.search-bar {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 16px;
}

.pager {
  display: flex;
  justify-content: flex-end;
}

.pager.spaced {
  margin-top: 16px;
}
.daily-times {
  display: flex;
  align-items: center;
  gap: 8px;
  flex-wrap: wrap;
}

.square-btn {
  border-radius: 2px;
}

.dialog-form .el-form-item {
  align-items: flex-start;
}
.dialog-form .el-form-item__label {
  padding-top: 6px;
}
.square-btn {
  border-radius: 2px;
}

/* 详情对话框样式 */
.detail-loading {
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 40px;
  gap: 12px;
  color: #909399;
}

.target-detail {
  padding: 8px 0;
}

.detail-header {
  display: flex;
  align-items: flex-start;
  gap: 16px;
  margin-bottom: 8px;
}

.detail-avatar {
  width: 80px;
  height: 80px;
  border-radius: 8px;
  object-fit: cover;
  flex-shrink: 0;
}

.detail-avatar-icon {
  width: 80px;
  height: 80px;
  color: #909399;
  flex-shrink: 0;
}

.detail-title {
  flex: 1;
  min-width: 0;
}

.detail-title h3 {
  margin: 0 0 8px 0;
  font-size: 20px;
  font-weight: 600;
  color: #1f2d3d;
}

.detail-signature {
  margin: 0;
  color: #606266;
  font-size: 14px;
  line-height: 1.5;
}

.detail-info {
  margin-top: 16px;
}

.text-muted {
  color: #909399;
}
</style>

