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
            <div class="content">
              <div class="main">
                <template v-if="activeTab === 'config'">
                  <!-- 账号配置（上） -->
                  <el-card style="margin-bottom: 16px">
                    <div class="card-title">账号配置</div>
                    <div class="search-bar compact">
                      <el-input
                        v-model="accountQuery"
                        size="small"
                        placeholder="模糊搜索名称"
                        style="width: 220px"
                        @keydown.enter="fetchAccounts"
                      />
                      <el-button size="small" type="primary" link @click="fetchAccounts" :loading="loading.accounts">
                        刷新
                      </el-button>
                      <el-button size="small" type="success" link @click="openAccountDialog()">
                        新增账号
                      </el-button>
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
                  <el-card>
                    <div class="card-title">公众号配置</div>
                    <div class="search-bar compact">
                      <el-input
                        v-model="targetQuery"
                        size="small"
                        placeholder="模糊搜索名称"
                        style="width: 220px"
                        @keydown.enter="fetchTargets"
                      />
                      <el-button size="small" type="primary" link @click="fetchTargets" :loading="loading.targets">
                        刷新
                      </el-button>
                      <el-button size="small" type="success" link @click="openTargetDialog()">
                        新增公众号
                      </el-button>
                    </div>
                    <el-table :data="targetsPaged" style="width: 100%; margin-top: 10px" size="small" stripe border>
                      <el-table-column fixed type="index" label="序号" width="60" />
                      <el-table-column prop="name" label="名称" width="180" />
                      <el-table-column label="调度" min-width="220">
                        <template #default="scope">{{ renderSchedule(scope.row) }}</template>
                      </el-table-column>
                      <el-table-column label="上次运行" width="180">
                        <template #default="scope">{{ formatTime(scope.row.last_run_at) }}</template>
                      </el-table-column>
                      <el-table-column prop="last_error" label="上次错误" min-width="240" />
                      <el-table-column label="操作" width="320" fixed="right">
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
                        :page-sizes="[5, 8, 10, 20]"
                        :page-size="targetsPageSize"
                        :total="targets.length"
                        :current-page="targetsPage"
                        @size-change="handleTargetSizeChange"
                        @current-change="handleTargetCurrentChange"
                      />
                    </div>
                  </el-card>
                </template>

                <template v-else-if="activeTab === 'articles'">
                  <el-card>
                    <div class="card-title">文章列表</div>
                    <div class="search-bar compact">
                      <el-input
                        v-model="articleQuery"
                        size="small"
                        placeholder="标题模糊搜索"
                        style="width: 240px"
                        @keydown.enter="fetchArticles"
                      />
                      <el-switch
                        v-model="todayOnly"
                        active-text="仅看今日"
                        style="margin-left: 8px"
                        @change="fetchArticles"
                      />
                      <el-radio-group v-model="articleView" size="small" style="margin-left: 8px" @change="onArticleViewChange">
                        <el-radio-button label="list">列表</el-radio-button>
                        <el-radio-button label="mp">公众号汇总</el-radio-button>
                      </el-radio-group>
                      <el-select v-model="articleSort" size="small" style="width: 140px; margin-left: 8px" @change="fetchArticles">
                        <el-option label="时间倒序" value="desc" />
                        <el-option label="时间正序" value="asc" />
                      </el-select>
                      <el-button size="small" type="primary" link style="margin-left: 8px" @click="fetchArticles" :loading="loading.articles">
                        刷新
                      </el-button>
                    </div>
                    <template v-if="articleView === 'list'">
                      <el-table :data="articlesPaged" style="width: 100%; margin-top: 10px" size="small" stripe border>
                        <el-table-column fixed type="index" label="序号" width="60" />
                        <el-table-column prop="mp_name" label="公众号" width="160" />
                        <el-table-column prop="title" label="标题" min-width="260" />
                        <el-table-column label="发布时间" width="180">
                          <template #default="scope">{{ formatTime(scope.row.publish_at) }}</template>
                        </el-table-column>
                        <el-table-column label="链接" width="160">
                          <template #default="scope">
                            <a :href="scope.row.url" target="_blank">打开</a>
                          </template>
                        </el-table-column>
                      </el-table>
                      <div class="pager spaced">
                        <el-pagination
                          background
                          small
                          layout="total, sizes, prev, pager, next, jumper"
                          :page-size="articlesPageSize"
                          :page-sizes="[20, 50, 100]"
                          :total="sortedArticles.length"
                          :current-page="articlesPage"
                          @size-change="handleArticleSizeChange"
                          @current-change="handleArticleCurrentChange"
                        />
                      </div>
                    </template>
                    <template v-else>
                      <el-table :data="mpSummary" style="width: 100%; margin-top: 10px" size="small" stripe border>
                        <el-table-column prop="mp_name" label="公众号" />
                        <el-table-column prop="count" label="文章数" width="100" />
                        <el-table-column label="最新发布时间">
                          <template #default="scope">{{ formatTime(scope.row.latest) }}</template>
                        </el-table-column>
                      </el-table>
                    </template>
                  </el-card>
                </template>

                <template v-else-if="activeTab === 'logs'">
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
                </template>
              </div>
            </div>
          </el-card>
        </el-main>
      </el-container>
    </el-container>

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
  </div>
</template>

<script setup>
import { ref, reactive, onMounted, computed } from "vue";
import dayjs from "dayjs";
import http from "../api/http";
import { ElMessage, ElMessageBox } from "element-plus";
import { useAuthStore } from "../stores/auth";
import { SettingOutlined, FileTextOutlined, ProfileOutlined } from "@ant-design/icons-vue";

const menuKeys = ref(["articles"]);
const accounts = ref([]);
const targets = ref([]);
const articles = ref([]);
const logs = ref([]);
const loading = ref({ accounts: false, targets: false, articles: false, logs: false });
const triggerLoading = reactive({});
const auth = useAuthStore();
const activeTab = ref("articles");
const accountQuery = ref("");
const targetQuery = ref("");
const articleQuery = ref("");
const logLimit = ref(200);
const articleView = ref("list"); // list | mp
const todayOnly = ref(false);
const articleSort = ref("desc"); // desc | asc
const accountsPage = ref(1);
const accountsPageSize = ref(8);
const targetsPage = ref(1);
const targetsPageSize = ref(8);
const articlesPage = ref(1);
const articlesPageSize = ref(20);
const logsPage = ref(1);
const logsPageSize = ref(10);

const accountDialog = reactive({
  visible: false,
  loading: false,
  isEdit: false,
  currentId: "",
  form: { name: "", token: "", cookie: "", login_account: "", login_password: "", remark: "" },
});

const targetDialog = reactive({
  visible: false,
  loading: false,
  isEdit: false,
  currentId: "",
  form: {
    name: "",
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

const fetchArticles = async () => {
  loading.value.articles = true;
  try {
    const params = { page: 1, page_size: 200, q: articleQuery.value };
    if (todayOnly.value) {
      const start = dayjs().startOf("day").toISOString();
      const end = dayjs().endOf("day").toISOString();
      params.start = start;
      params.end = end;
    }
    const { data } = await http.get("/articles", { params });
    articles.value = data.items || [];
  } catch {
    ElMessage.error("获取文章失败");
  } finally {
    loading.value.articles = false;
  }
};

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

const trigger = async (row) => {
  triggerLoading[row.id] = true;
  try {
    await http.post(`/targets/${row.id}/run`);
    ElMessage.success(`已下发任务：${row.name}`);
    fetchTargets();
    fetchLogs();
  } catch (e) {
    ElMessage.error(e?.response?.data?.message || "下发失败");
  } finally {
    triggerLoading[row.id] = false;
  }
};

const logout = () => {
  auth.clear();
  window.location.href = "/login";
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

const sortedArticles = computed(() => {
  const arr = [...(articles.value || [])];
  return arr.sort((a, b) => {
    const ta = new Date(a.publish_at || a.created_at || 0).getTime();
    const tb = new Date(b.publish_at || b.created_at || 0).getTime();
    return articleSort.value === "asc" ? ta - tb : tb - ta;
  });
});

const articlesPaged = computed(() => {
  const start = (articlesPage.value - 1) * articlesPageSize.value;
  return sortedArticles.value.slice(start, start + articlesPageSize.value);
});

const mpSummary = computed(() => {
  const map = new Map();
  sortedArticles.value.forEach((item) => {
    const key = item.mp_name || "未知";
    const ts = new Date(item.publish_at || item.created_at || 0).getTime();
    if (!map.has(key)) {
      map.set(key, { mp_name: key, count: 0, latest: 0 });
    }
    const obj = map.get(key);
    obj.count += 1;
    obj.latest = Math.max(obj.latest, ts);
  });
  return Array.from(map.values()).sort((a, b) => b.count - a.count);
});

const onArticleViewChange = () => {
  // no-op for now; could add different fetch params by view
};

const accountsPaged = computed(() => {
  const start = (accountsPage.value - 1) * accountsPageSize.value;
  return accounts.value.slice(start, start + accountsPageSize.value);
});

const targetsPaged = computed(() => {
  const start = (targetsPage.value - 1) * targetsPageSize.value;
  return targets.value.slice(start, start + targetsPageSize.value);
});

const logsPaged = computed(() => {
  const start = (logsPage.value - 1) * logsPageSize.value;
  return logs.value.slice(start, start + logsPageSize.value);
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
const handleArticleSizeChange = (val) => {
  articlesPageSize.value = val;
  articlesPage.value = 1;
};
const handleArticleCurrentChange = (val) => {
  articlesPage.value = val;
};
const handleLogSizeChange = (val) => {
  logsPageSize.value = val;
  logsPage.value = 1;
};
const handleLogCurrentChange = (val) => {
  logsPage.value = val;
};


onMounted(() => {
  fetchAccounts();
  fetchTargets();
  fetchArticles();
  fetchLogs();
});

const onSelect = ({ key }) => {
  menuKeys.value = [key];
  activeTab.value = key;
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
.card-title {
  font-weight: bold;
  margin-bottom: 8px;
  display: flex;
  align-items: center;
  gap: 8px;
}
.content {
  display: block;
}
.main {
  width: 100%;
}
.brand {
  display: flex;
  align-items: center;
  gap: 10px;
  font-weight: 600;
  font-size: 16px;
}
.brand-title {
  color: #1f2d3d;
}
.header-actions {
  display: flex;
  align-items: center;
  gap: 8px;
}
.el-card {
  border-radius: 12px;
}
.el-button {
  border-radius: 8px;
}
.square-btn {
  border-radius: 2px;
}
.main-shell {
  padding-top: 12px;
}
.card-shell {
  border: none;
  box-shadow: 0 10px 30px rgba(0, 0, 0, 0.05);
  width: 100%;
}
.aside {
  background: #fff;
  border-right: 1px solid #ebeef5;
  padding-top: 12px;
}
.daily-times {
  display: flex;
  align-items: center;
  gap: 8px;
  flex-wrap: wrap;
}
.dialog-form .el-form-item {
  align-items: flex-start;
}
.dialog-form .el-form-item__label {
  padding-top: 6px;
}
.tiny-tag {
  padding: 0 4px;
  height: 16px;
  line-height: 16px;
  font-size: 10px;
}
.sub-hint {
  margin: 6px 0 2px;
  color: #909399;
  font-size: 12px;
}
.search-bar.compact {
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

